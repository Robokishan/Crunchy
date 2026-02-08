"""
Test Tracxn parser and extractors against saved HTML.

With DUMP_RAW_SCRAPED_DATA=true, the crawler writes:
  raw_scraped_dumps/<company_name>_tracxy.json
  raw_scraped_dumps/<company_name>_crunchbase.json
Load a Tracxn dump and use the "html" key here to test TracxnDataParser or
tracxnExtractor without hitting Tracxn. Competitors/Alternates extraction is
tested here: after changing XPATH_COMPETITORS_HREF or XPATH_ALTERNATES_HREF in
TracxnDataParser, re-run this script with a Tracxn dump to verify without re-scraping.

Usage:
  # From a dumped JSON (after scraping with DUMP_RAW_SCRAPED_DATA=true):
  python -c "
  import json, sys
  sys.path.insert(0, 'CrunchyCrawler')
  from utility.test_tracxy_extractor import run_from_dump
  run_from_dump('raw_scraped_dumps/the_level_tracxy.json')
  "

  # Or run this file with inline HTML / path to dump:
  python test_tracxy_extractor.py [path/to/dump.json]
"""

__package__ = "CrunchyCrawler"

import json
import os
import sys

# Allow imports from CrunchyCrawler when run as script
_script_dir = os.path.dirname(os.path.abspath(__file__))
_crawler_root = os.path.dirname(os.path.dirname(_script_dir))
if _crawler_root not in sys.path:
    sys.path.insert(0, _crawler_root)

from scrapy.selector import Selector

from CrunchyCrawler.parser.TracxnDataParser import TracxnDataParser
from CrunchyCrawler.extractors.tracxnExtractor import (
    CompanyDetails,
    DetailsExtract,
    HighlightsExtract,
)

# Same extractors as in TracxnDataParser (parser references these for section-based extraction)
TRACXN_EXTRACTORS = [CompanyDetails, DetailsExtract, HighlightsExtract]


def run_from_dump(dump_path: str) -> dict:
    """Load a JSON dump (from DUMP_RAW_SCRAPED_DATA) and run Tracxn parser + extractors."""
    with open(dump_path, encoding="utf-8") as f:
        data = json.load(f)
    html = data.get("html", "")
    source = data.get("source", "")
    if source != "tracxn":
        print(
            f"Warning: dump source is '{source}', expected 'tracxn'. Continuing anyway."
        )
    page_url = data.get("url") or data.get("parsed_item", {}).get("tracxn_url") or ""
    return run_on_html(html, page_url=page_url)


def run_on_html(html: str, page_url: str = "") -> dict:
    """Run TracxnDataParser and tracxn extractors on the given HTML string."""
    x = Selector(text=html)

    # 1) Main parser (what the spider uses)
    item = TracxnDataParser.extract_item(x)
    print("TracxnDataParser.extract_item:", item)

    # 2) Section extractors (tracxnExtractor) – expect list of HTML chunks; pass full page
    for ext_cls in TRACXN_EXTRACTORS:
        try:
            val = ext_cls().getValue(text=[html])
            if val:
                item.update(val)
                # print(f"  + {ext_cls.__name__}: {val}")
        except Exception as e:
            print(f"  {ext_cls.__name__} error: {e}")

    # 3) Competitors/Alternates (same as spider; use page_url to exclude self)
    competitor_urls = TracxnDataParser.extract_competitors_and_alternates(
        x, page_url or "https://tracxn.com/"
    )
    item["competitor_urls"] = competitor_urls
    n = len(competitor_urls)
    # print(f"Competitor/alternate URLs ({n}):")
    # for u in competitor_urls:
    #     print(f"  {u}")

    return item


if __name__ == "__main__":
    if len(sys.argv) > 1:
        dump_path = sys.argv[1]
        if os.path.isfile(dump_path):
            run_from_dump(dump_path)
        else:
            print(f"File not found: {dump_path}")
            sys.exit(1)
    else:
        # No dump path: use minimal inline Tracxn-like HTML for quick test
        sample_html = """
        <div class="txn--seo-companies__detail txn--display-flex-row">
            <dd class="txn--seo-companies__details__value">
                <a href="https://thelevel.ai/">thelevel.ai</a>
            </dd>
        </div>
        <h1>The Level - Company Profile</h1>
        """
        run_on_html(sample_html, page_url="https://tracxn.com/")
