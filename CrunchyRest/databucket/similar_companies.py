"""
Centralized logic: push similar/competitor company URLs to crawl queue only when
the company's industries intersect the configured interested industries.

Used by both Crunchbase and Tracxn databucket consumers after they have the
merged view (industries + list of similar/competitor URLs).
"""

from databucket.models import Crunchbase, InterestedIndustries, TracxnRaw
from rabbitmq.apps import RabbitMQManager


def publish_similar_companies_if_interested(
    industries: list,
    similar_urls: list,
    entry_point: str = "crunchbase",
) -> None:
    """
    If company industries intersect interested industries, push each similar/competitor
    URL to the appropriate crawl queue (CB or Tracxn). Skip URLs already in DB.
    Logs skip reasons and push/skip per URL.
    """
    interested = InterestedIndustries.get_interested_industries()
    if not interested:
        print("  - Skipping similar company push: no interested industries configured")
        return

    # Ensure industry values are strings for set intersection
    industries_set = set(str(x) for x in (industries or []) if x is not None)
    interested_set = set(str(x) for x in interested if x is not None)
    if not (industries_set & interested_set):
        print("  - Skipping similar company push: industries not in interested list")
        return

    # Only process string URLs; skip non-strings to avoid AttributeError
    similar_urls = [
        (u if isinstance(u, str) else str(u)).strip().rstrip("/")
        for u in (similar_urls or [])
        if u is not None
    ]
    similar_urls = [u for u in similar_urls if u]
    if not similar_urls:
        print("  - Skipping similar company push: no similar companies")
        return

    for url in similar_urls:
        if not url:
            continue
        if "crunchbase.com" in url:
            try:
                Crunchbase.objects.get(crunchbase_url=url)
                print(f"  - Already in Crunchbase, skipping: {url}")
                continue
            except Crunchbase.DoesNotExist:
                pass
            try:
                RabbitMQManager.publish_crunchbase_crawl(
                    {"url": url, "entry_point": entry_point}
                )
                print(f"  - Pushing similar company (CB) to queue: {url}")
            except Exception as e:
                print(f"  - Failed to push CB URL {url}: {e}")
        elif "tracxn.com" in url:
            try:
                TracxnRaw.objects.get(tracxn_url=url)
                print(f"  - Competitor already in TracxnRaw, skipping: {url}")
                continue
            except TracxnRaw.DoesNotExist:
                pass
            try:
                RabbitMQManager.publish_tracxn_crawl(
                    {"url": url, "entry_point": entry_point}
                )
                print(f"  - Pushing similar company (Tracxn) to queue: {url}")
            except Exception as e:
                print(f"  - Failed to push Tracxn URL {url}: {e}")
