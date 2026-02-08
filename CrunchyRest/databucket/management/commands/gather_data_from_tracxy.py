"""
Consume Tracxn scraped items from RabbitMQ databucket queue.

Saves to TracxnRaw, merges into Crunchbase. Discovers Crunchbase URL (DuckDuckGo)
and pushes to crawl queue only when entry_point != "crunchbase". When we discover
a CB URL from Tracxn we create/update Crunchbase from Tracxn data so merge works
when scrape starts from Tracxn; the CB consumer will update that record when the
CB page is scraped. Competitor/alternate URLs from Tracxn are pushed to the crawl queue.

Usage:
    python manage.py gather_data_from_tracxy
"""

from django.core.management import BaseCommand
from django.conf import settings
from rabbitmq.apps import RabbitMQManager
from rabbitmq.databucket_consumer import run_consumer
from databucket.models import Crunchbase, TracxnRaw
from databucket.discovery import discover_crunchbase_url
from utils.domain import normalize_domain
from utils.Currency import CurrencyConverter
import regex as re
import pycountry


class Command(BaseCommand):
    help = 'Consume Tracxn data from RabbitMQ databucket queue and save to MongoDB'

    def handle(self, *args, **options):
        self.stdout.write('Starting Tracxn RabbitMQ consumer...')
        RabbitMQManager.connect_to_rabbitmq()
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
            rate = 1  # no conversion = 1:1 (e.g. already USD)

            if funding_total:
                result = self.get_currency_in_usd(funding_total)
                if result:
                    funding_total_usd, rate = result

            website = (data.get('website') or '').strip().rstrip('/')
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

            # merged_with_crunchbase: True if a Crunchbase with same domain exists (for analytics)
            # Avoid .exists() — djongo/sqlparse can hit RecursionError on the generated SQL.
            has_cb = (
                Crunchbase.objects.filter(normalized_domain=normalized).first() is not None
                if normalized
                else False
            )
            competitor_urls = data.get('competitor_urls') or []
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
                'merged_with_crunchbase': has_cb,
                'similar_companies': competitor_urls,
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
                merge_qs = Crunchbase.objects.filter(normalized_domain=normalized)
                merge_count = merge_qs.count()
                print(f"  - [Merge] filter(Crunchbase.objects, normalized_domain={repr(normalized)}) -> {merge_count} record(s)")
                if merge_count:
                    for cb in merge_qs[:3]:
                        print(f"    -> CB: crunchbase_url={repr(cb.crunchbase_url)}, name={repr(cb.name)}")
                else:
                    print(f"  - [Merge] No Crunchbase row with normalized_domain={repr(normalized)} (merge will not update any row)")
                # Merge: overwrite Crunchbase with Tracxn values (same as funding). similar_companies from TracxnRaw (we just saved it).
                update_kw = {
                    'funding': funding_total or '',
                    'funding_usd': funding_total_usd,
                    'rate': rate,
                    'merged_with_tracxn': True,
                    'tracxn_url': tracxn_url,
                    'similar_companies': getattr(tracxn_record, 'similar_companies', None) or [],
                }
                if website:
                    update_kw['website'] = website
                founded_tracxn = (data.get('founded') or '').strip()
                if founded_tracxn:
                    update_kw['founded'] = founded_tracxn
                updated = merge_qs.update(**update_kw)
                if updated:
                    parts = ['funding', 'funding_usd']
                    if website:
                        parts.append('website')
                    if founded_tracxn:
                        parts.append('founded')
                    if 'rate' in update_kw:
                        parts.append('rate')
                    if 'merged_with_tracxn' in update_kw:
                        parts.append('merged_with_tracxn')
                    if update_kw.get('tracxn_url'):
                        parts.append('tracxn_url')
                    if update_kw.get('similar_companies'):
                        parts.append('similar_companies')
                    print(f"  - [Merge] Updated {updated} Crunchbase record(s): {', '.join(parts)}")
                else:
                    print(f"  - [Merge] Updated 0 rows (no Crunchbase record with normalized_domain={repr(normalized)})")
            else:
                print(f"  - [Merge] Skipped: no normalized_domain (website={repr(website)})")

            # Cross-discovery: find Crunchbase URL and push to queue only when this is NOT the first loop (entry_point=crunchbase).
            # Do NOT create a Crunchbase row here: databucket_crunchbase should only have rows when we actually scraped Crunchbase (or when CB + Tracxn are merged). When CB is scraped later, the CB consumer will create the row.
            if data.get("entry_point") != "crunchbase" and normalized:
                crunchbase_url = discover_crunchbase_url(
                    data.get('name', ''),
                    normalized,
                )
                if crunchbase_url:
                    crunchbase_url = crunchbase_url.strip().rstrip('/')
                    print(f"  - Discovered Crunchbase URL, pushing to queue: {crunchbase_url}")
                    RabbitMQManager.publish_crunchbase_crawl({"url": crunchbase_url, "entry_point": "tracxn"})

            # Push competitor/alternate URLs to crawl queue (skip if already in TracxnRaw)
            for tracxn_url in data.get("competitor_urls", []) or []:
                try:
                    TracxnRaw.objects.get(tracxn_url=tracxn_url)
                    print(f"  - Competitor already in TracxnRaw, skipping: {tracxn_url}")
                except TracxnRaw.DoesNotExist:
                    print(f"  - Pushing competitor to queue: {tracxn_url}")
                    RabbitMQManager.publish_tracxn_crawl({"url": tracxn_url, "entry_point": "tracxn"})

            return True

        except Exception as e:
            print(f"Error processing Tracxn data: {e}")
            import traceback
            traceback.print_exc()
            return False
