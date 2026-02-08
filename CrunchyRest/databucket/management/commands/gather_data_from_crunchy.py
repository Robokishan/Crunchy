"""
Consume Crunchbase scraped items from RabbitMQ databucket queue.

Saves to Crunchbase collection, pushes similar companies and discovered
Tracxn URLs to the crawl queue.

Usage:
    python manage.py gather_data_from_crunchy
"""

from django.core.management import BaseCommand
from django.conf import settings
from rabbitmq.apps import RabbitMQManager
from rabbitmq.databucket_consumer import run_consumer
from databucket.models import Crunchbase
from databucket.models import InterestedIndustries
from databucket.discovery import discover_tracxn_url
from utils.domain import normalize_domain
import regex as re
from utils.Currency import CurrencyConverter
import pycountry


class Command(BaseCommand):
    help = 'Consume Crunchbase data from RabbitMQ databucket queue and save to MongoDB'

    def handle(self, *args, **options):
        # Ensure RabbitMQ connection exists (for publish_message in callback)
        RabbitMQManager.connect_to_rabbitmq()
        run_consumer(
            queue_name=settings.RB_DATABUCKET_CRUNCHBASE_QUEUE,
            routing_key=settings.RB_DATABUCKET_CRUNCHBASE_RK,
            exchange=settings.RB_DATABUCKET_EXCHANGE,
            callback=self.callback,
        )

    # TODO: dirty code to be refactored

    def get_currency_in_usd(self, funding):
        try:
            currencyConvert = CurrencyConverter()
            currency_symbol = currencyConvert.get_currency_symbol(funding)
            currency_code = None
            currency_amount = None

            # handle currency with symbols
            if len(currency_symbol) > 0:
                currency_symbol = currency_symbol[-1]
                amount_str = funding.split(currency_symbol)[-1]
                # sample $1.5M, €1.5M, £1.5M, ¥1.5M, ₹1.5M
                match = re.match(r'([\d\.]+)([A-Za-z]?)', amount_str)
                if match:
                    number, multiplier = match.groups()
                    currency_amount = float(
                        number) * currencyConvert.get_multiplier(multiplier)
                    currency_code = currencyConvert.symbol_to_currency_code(
                        currency_symbol)

            # handle currency with currency code
            elif funding and funding != '—':
                # sample USD1.5M, EUR1.5M, GBP1.5M, JPY1.5M, INR1.5M
                currency_code_pattern = re.compile(
                    r'([A-Z]{3})(\d+(\.\d+)?)([A-Za-z]?)')
                match = currency_code_pattern.match(funding)
                if match:
                    currency_code, amount, _, suffix = match.groups()
                    currency_amount = float(
                        amount) * currencyConvert.get_multiplier(suffix)
                    currency_code = pycountry.currencies.get(
                        alpha_3=currency_code).alpha_3

            if currency_amount and currency_code:
                currency_amount_usd, rate = currencyConvert.convert(
                    currency_amount, currency_code, 'USD')
                return currency_amount_usd, rate, currency_code, currency_amount
        except Exception as e:
            print(f"Currency Conversion: {e}")
        return None

    def callback(self, data):
        try:
            if data.get('funding'):
                result = self.get_currency_in_usd(data['funding'])
                if result is not None:
                    currency_amount_usd, rate, _, _ = result
                    data['funding_usd'] = currency_amount_usd
                    data['rate'] = rate
                else:
                    data['funding_usd'] = 0
                    data['rate'] = 0
            else:
                data['funding_usd'] = 0
                data['rate'] = 0

            industries = [industry.strip()
                          for industry in data.get('industries', [])]

            # Normalize the website domain for entity matching
            website = data.get('website')
            normalized = normalize_domain(website) if website else None

            defaults = {
                'name': data.get('name'),
                'website': website,
                'logo': data.get('logo'),
                'founders': data.get('founders', []),
                'similar_companies': data.get('similar_companies', []),
                'description': data.get('description'),
                'long_description': data.get('long_description'),
                'acquired': data.get('acquired'),
                'industries': industries,
                'founded': data.get('founded'),
                'lastfunding': data.get('lastfunding'),
                'stocksymbol': data.get('stock_symbol'),
                'normalized_domain': normalized,
            }

            if data.get('funding_usd', 0) != 0:
                defaults['funding_usd'] = data['funding_usd']
                defaults['rate'] = data['rate']

            _funding = data.get('funding', 0)
            if _funding != 0:
                defaults['funding'] = data.get('funding')

            crunchbase, created = Crunchbase.objects.update_or_create(
                crunchbase_url=data['crunchbase_url'],
                defaults=defaults
            )
            print("Created:", crunchbase, created, data)

            # Only push similar companies to queue if InterestedIndustries config exists
            interested_industries = InterestedIndustries.objects.filter(
                key='industry'
            ).first()
            if interested_industries is not None:
                print("Interested Industries:", interested_industries.industries)
                send_similar_companies = False
                for industry in industries:
                    if industry in interested_industries.industries:
                        send_similar_companies = True
                if data.get('similar_companies') and send_similar_companies:
                    for company in data['similar_companies']:
                        try:
                            Crunchbase.objects.get(crunchbase_url=company)
                            print("Company already found", company)
                        except Crunchbase.DoesNotExist:
                            print("sending company back to queue", company)
                            RabbitMQManager.publish_message(company)
            else:
                print("InterestedIndustries (key='industry') not configured; skipping similar-companies queue push")

            # Cross-discovery - find Tracxn URL for this company
            if normalized:
                tracxn_url = discover_tracxn_url(
                    company_name=data.get('name', ''),
                    domain=normalized
                )
                if tracxn_url:
                    print(f"Discovered Tracxn URL, pushing to queue: {tracxn_url}")
                    RabbitMQManager.publish_message(tracxn_url)

            return True
        except Exception as e:
            print("Error", e)
            return False
