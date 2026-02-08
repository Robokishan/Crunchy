"""
Test Crunchbase parser against saved HTML.

With DUMP_RAW_SCRAPED_DATA=true, the crawler writes:
  raw_scraped_dumps/<company_name>_crunchbase.json
  raw_scraped_dumps/<company_name>_tracxy.json
Set COMPANY_NAME below and run this script to load the Crunchbase dump and run
CrunchbaseDataParser on the root HTML (no individual extractors — the parser
handles profile-section extraction internally).

Run from CrunchyCrawler project root (parent of CrunchyCrawler/):

  PYTHONPATH=. python CrunchyCrawler/utility/test_crunchy_extractor.py

Or as a module:

  cd CrunchyCrawler && PYTHONPATH=. python -m CrunchyCrawler.utility.test_crunchy_extractor
"""

import json
import os

# --- Set this to the company name (dump file will be <COMPANY_NAME>_crunchbase.json) ---
COMPANY_NAME = "hofy"

# Dump directory: raw_scraped_dumps at project root (CrunchyCrawler/raw_scraped_dumps)
_script_dir = os.path.dirname(os.path.abspath(__file__))
DUMP_DIR = os.path.join(_script_dir, "..", "..", "raw_scraped_dumps")

from scrapy.selector import Selector

from CrunchyCrawler.parser.CrunchbaseDataParser import CrunchbaseDataParser


def load_html_from_dump(company_name: str, dump_dir: str) -> str:
    """Load raw_scraped_dumps/<company_name>_crunchbase.json and return the 'html' string."""
    path = os.path.join(dump_dir, f"{company_name}_crunchbase.json")
    if not os.path.isfile(path):
        raise FileNotFoundError(
            f"Dump not found: {path}. Set DUMP_RAW_SCRAPED_DATA=true and scrape Crunchbase first."
        )
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    html = data.get("html", "")
    if not html:
        raise ValueError(f"No 'html' key in {path}")
    return html


if __name__ == "__main__":
    html = load_html_from_dump(COMPANY_NAME, DUMP_DIR)
    x = Selector(text=html)
    item = CrunchbaseDataParser.extract_item(x)
    print(item)
