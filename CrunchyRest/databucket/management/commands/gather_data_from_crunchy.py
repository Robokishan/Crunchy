"""
Consume Crunchbase scraped items from RabbitMQ databucket queue.

Saves to Crunchbase collection. Discovers Tracxn URL (DuckDuckGo) and pushes
to crawl queue only when entry_point != "tracxn" (i.e. not when we came from Tracxn).
We never push similar/competitor companies from Crunchbase.

Usage:
    python manage.py gather_data_from_crunchy
"""

from django.core.management import BaseCommand
from django.conf import settings
from rabbitmq.apps import RabbitMQManager
from rabbitmq.databucket_consumer import run_consumer
from databucket.models import Crunchbase, TracxnRaw
from databucket.discovery import discover_tracxn_url
from utils.domain import normalize_domain
import regex as re
from utils.Currency import CurrencyConverter
import pycountry


class Command(BaseCommand):
    help = "Consume Crunchbase data from RabbitMQ databucket queue and save to MongoDB"

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
                match = re.match(r"([\d\.]+)([A-Za-z]?)", amount_str)
                if match:
                    number, multiplier = match.groups()
                    currency_amount = float(number) * currencyConvert.get_multiplier(
                        multiplier
                    )
                    currency_code = currencyConvert.symbol_to_currency_code(
                        currency_symbol
                    )

            # handle currency with currency code
            elif funding and funding != "—":
                # sample USD1.5M, EUR1.5M, GBP1.5M, JPY1.5M, INR1.5M
                currency_code_pattern = re.compile(
                    r"([A-Z]{3})(\d+(\.\d+)?)([A-Za-z]?)"
                )
                match = currency_code_pattern.match(funding)
                if match:
                    currency_code, amount, _, suffix = match.groups()
                    currency_amount = float(amount) * currencyConvert.get_multiplier(
                        suffix
                    )
                    currency_code = pycountry.currencies.get(
                        alpha_3=currency_code
                    ).alpha_3

            if currency_amount and currency_code:
                currency_amount_usd, rate = currencyConvert.convert(
                    currency_amount, currency_code, "USD"
                )
                return currency_amount_usd, rate, currency_code, currency_amount
        except Exception as e:
            print(f"Currency Conversion: {e}")
        return None

    def callback(self, data):
        try:
            industries = [industry.strip() for industry in data.get("industries", [])]

            # Normalize the website domain for entity matching; strip trailing slash
            website = data.get("website")
            if website:
                website = website.strip().rstrip("/")
            normalized = normalize_domain(website) if website else None

            defaults = {
                "name": data.get("name"),
                "website": website,
                "logo": data.get("logo"),
                "founders": data.get("founders", []),
                "similar_companies": data.get("similar_companies", []),
                "description": data.get("description"),
                "long_description": data.get("long_description"),
                "acquired": data.get("acquired"),
                "industries": industries,
                "lastfunding": data.get("lastfunding"),
                "stocksymbol": data.get("stock_symbol"),
                "normalized_domain": normalized,
            }

            # Funding and founded: never from CB (not reliable). Use Tracxn when available.
            tracxn = (
                TracxnRaw.objects.filter(normalized_domain=normalized).first()
                if normalized
                else None
            )
            if tracxn:
                defaults["funding"] = (tracxn.funding_total or "").strip() or ""
                defaults["funding_usd"] = getattr(tracxn, "funding_total_usd", 0) or 0
                # Rate from conversion: 1 when already USD, actual rate when converted
                funding_str = (tracxn.funding_total or "").strip()
                if funding_str:
                    result = self.get_currency_in_usd(funding_str)
                    defaults["rate"] = result[1] if result else 1
                else:
                    defaults["rate"] = 1
                defaults["founded"] = (tracxn.founded or "").strip() or ""
            else:
                defaults["funding"] = ""
                defaults["funding_usd"] = 0
                defaults["rate"] = 1
                defaults["founded"] = ""

            # Normalize crunchbase_url (no trailing slash) so we match the same record as Tracxn consumer
            crunchbase_url = (data.get("crunchbase_url") or "").strip().rstrip("/")
            crunchbase, created = Crunchbase.objects.update_or_create(
                crunchbase_url=crunchbase_url, defaults=defaults
            )
            print("Created:", crunchbase, created, data)

            # Log merge lookup: when Crunchbase data is received, how many CB vs Tracxn records share this normalized_domain (for merge debugging)
            if normalized:
                cb_with_domain = Crunchbase.objects.filter(normalized_domain=normalized)
                tracxn_with_domain = TracxnRaw.objects.filter(
                    normalized_domain=normalized
                )
                cb_n = cb_with_domain.count()
                tx_n = tracxn_with_domain.count()
                print(
                    f"  - Merge lookup: normalized_domain={repr(normalized)} -> Crunchbase records={cb_n}, TracxnRaw records={tx_n}"
                )
                if cb_n:
                    for o in cb_with_domain[:2]:
                        print(
                            f"    -> CB: crunchbase_url={repr(o.crunchbase_url)}, name={repr(getattr(o, 'name', None))}"
                        )
                if tx_n:
                    for o in tracxn_with_domain[:2]:
                        print(
                            f"    -> Tracxn: tracxn_url={repr(getattr(o, 'tracxn_url', None))}, name={repr(getattr(o, 'name', None))}"
                        )

            # Cross-discovery: find Tracxn URL only when this CB page was not discovered from Tracxn
            if data.get("entry_point") != "tracxn" and normalized:
                tracxn_url = discover_tracxn_url(
                    company_name=data.get("name", ""), domain=normalized
                )
                if tracxn_url:
                    print(f"Discovered Tracxn URL, pushing to queue: {tracxn_url}")
                    RabbitMQManager.publish_message(
                        {"url": tracxn_url, "entry_point": "crunchbase"}
                    )

            return True
        except Exception as e:
            print("Error", e)
            return False
