from django.core.management import BaseCommand
from rabbitmq.apps import RabbitMQManager
from databucket.models import Crunchbase
from databucket.models import InterestedIndustries
from kafka.consumer import Subscriber
import regex as re
from utils.Currency import CurrencyConverter
import pycountry


class Command(BaseCommand):
    def handle(self, *args, **options):
        subscriber = Subscriber(callback=self.callback)
        subscriber.connect()
        subscriber.run()

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
            defaults = {
                'name': data.get('name'),
                'website': data.get('website'),
                'logo': data.get('logo'),
                'founders': data.get('founders', []),
                'similar_companies': data.get('similar_companies', []),
                'description': data.get('description'),
                'long_description': data.get('long_description'),
                'acquired': data.get('acquired'),
                'industries': industries,
                'founded': data.get('founded'),
                'lastfunding': data.get('lastfunding'),
                'stocksymbol': data.get('stock_symbol')
            }

            if data.get('funding_usd', 0) != 0:
                defaults['funding_usd'] = data.get('funding_usd')
                defaults['rate'] = data.get('rate')

            _funding = data.get('funding', 0)
            if _funding != 0:
                defaults['funding'] = data.get('funding')

            crunchbase, created = Crunchbase.objects.update_or_create(
                crunchbase_url=data['crunchbase_url'],
                defaults=defaults
            )
            print("Created:", crunchbase, created, data)

            interested_industries = InterestedIndustries.objects.get(
                key='industry')

            print("Interested Industries:", interested_industries.industries)

            send_similar_companies = False

            # if any industries is inside interested industries then print included
            for industry in industries:
                if industry in interested_industries.industries:
                    send_similar_companies = True

            if data.get('similar_companies') and send_similar_companies == True:
                for company in data['similar_companies']:
                    try:
                        isFound = Crunchbase.objects.get(
                            crunchbase_url=company)
                        print("Company already found",
                              isFound, company)
                    except Exception as e:
                        # this company didn't found in database
                        print("sending company back to queue", company)
                        RabbitMQManager.publish_message(company)

            return True
        except Exception as e:
            print("Error", e)
            return False
