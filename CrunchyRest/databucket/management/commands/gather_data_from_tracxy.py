"""
Consume Tracxn scraped items from RabbitMQ databucket queue.

Saves to TracxnRaw collection.

Usage:
    python manage.py gather_data_from_tracxy
"""

from django.core.management import BaseCommand
from django.conf import settings
from rabbitmq.databucket_consumer import run_consumer
from databucket.models import Crunchbase, TracxnRaw
from utils.domain import normalize_domain
from utils.Currency import CurrencyConverter
import regex as re
import pycountry


class Command(BaseCommand):
    help = 'Consume Tracxn data from RabbitMQ databucket queue and save to MongoDB'

    def handle(self, *args, **options):
        self.stdout.write('Starting Tracxn RabbitMQ consumer...')
        run_consumer(
            queue_name=settings.RB_DATABUCKET_TRACXN_QUEUE,
            routing_key=settings.RB_DATABUCKET_TRACXN_RK,
            exchange=settings.RB_DATABUCKET_EXCHANGE,
            callback=self.callback,
        )

    def get_currency_in_usd(self, funding: str) -> tuple | None:
        if not funding or funding == '—':
            return None

        try:
            currencyConvert = CurrencyConverter()
            currency_symbol = currencyConvert.get_currency_symbol(funding)
            currency_code = None
            currency_amount = None

            if len(currency_symbol) > 0:
                currency_symbol = currency_symbol[-1]
                amount_str = funding.split(currency_symbol)[-1]
                match = re.match(r'([\d\.]+)([A-Za-z]?)', amount_str)
                if match:
                    number, multiplier = match.groups()
                    currency_amount = float(
                        number) * currencyConvert.get_multiplier(multiplier)
                    currency_code = currencyConvert.symbol_to_currency_code(
                        currency_symbol)
            else:
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
                return currency_amount_usd, rate

        except Exception as e:
            print(f"Currency Conversion Error: {e}")

        return None

    def callback(self, data: dict) -> bool:
        try:
            tracxn_url = data.get('tracxn_url')
            if not tracxn_url:
                print("No tracxn_url in data, skipping")
                return True

            funding_total = data.get('funding_total', '')
            funding_total_usd = 0

            if funding_total:
                result = self.get_currency_in_usd(funding_total)
                if result:
                    funding_total_usd, _ = result

            website = data.get('website', '')
            normalized = normalize_domain(website) if website else None

            funding_rounds = data.get('funding_rounds', [])
            processed_rounds = []
            for round_data in funding_rounds:
                processed_round = dict(round_data)
                if 'amount' in round_data:
                    result = self.get_currency_in_usd(round_data['amount'])
                    if result:
                        processed_round['amount_usd'] = result[0]
                processed_rounds.append(processed_round)

            defaults = {
                'name': data.get('name', ''),
                'website': website,
                'normalized_domain': normalized,
                'funding_total': funding_total,
                'funding_total_usd': funding_total_usd,
                'funding_rounds': processed_rounds,
                'founders': data.get('founders', []),
                'description': data.get('description', ''),
                'logo': data.get('logo', ''),
                'founded': data.get('founded', ''),
                'hq_location': data.get('hq_location', ''),
                'matched': False,
            }

            tracxn_record, created = TracxnRaw.objects.update_or_create(
                tracxn_url=tracxn_url,
                defaults=defaults
            )

            action = "Created" if created else "Updated"
            print(f"{action}: {tracxn_record.name} ({tracxn_url})")
            print(f"  - Funding: {funding_total} -> ${funding_total_usd:,.0f} USD")
            print(f"  - Domain: {normalized}")
            print(f"  - Rounds: {len(processed_rounds)}")

            # Merge into Crunchbase (source of truth for UI): update funding, funding_usd, website, founded
            if normalized:
                update_kw = {
                    'funding': funding_total or '',
                    'funding_usd': funding_total_usd,
                }
                if website:
                    update_kw['website'] = website
                founded_tracxn = (data.get('founded') or '').strip()
                if founded_tracxn:
                    update_kw['founded'] = founded_tracxn
                updated = Crunchbase.objects.filter(normalized_domain=normalized).update(**update_kw)
                if updated:
                    parts = ['funding', 'funding_usd']
                    if website:
                        parts.append('website')
                    if founded_tracxn:
                        parts.append('founded')
                    print(f"  - Merged into Crunchbase ({updated} record(s)): {', '.join(parts)}")

            return True

        except Exception as e:
            print(f"Error processing Tracxn data: {e}")
            import traceback
            traceback.print_exc()
            return False
