"""
TracxnDataParser - Parses company data from Tracxn company pages.

Tracxn URL pattern: https://tracxn.com/d/companies/<slug>/__<hash>#about-the-company

This parser extracts:
- Company name, website, description, logo
- Funding total
- Founders
- Founded date, industries
- Competitors and alternates (company profile URLs) via configurable XPaths
"""

from scrapy.selector import Selector
from CrunchyCrawler.extractors.tracxnExtractor import DetailsExtract
from CrunchyCrawler.extractors.tracxnExtractor import CompanyDetails
from CrunchyCrawler.extractors.tracxnExtractor import HighlightsExtract
import regex as re

# list of all extractors add if any new extractor come for tracxn
extractors = [CompanyDetails, DetailsExtract, HighlightsExtract]

# ---------------------------------------------------------------------------
# Competitors / Alternates: EDIT ONLY THESE XPATHS if the page structure changes.
# Each must return @href values for links to Tracxn company pages (/d/companies/...).
# Use browser DevTools to find the right selector, then paste the XPath for href only.
# ---------------------------------------------------------------------------
XPATH_COMPETITORS_HREF = (
    "//*[contains(normalize-space(), 'Competitors')]/following-sibling::*[1]"
    "//a[contains(@href, '/d/companies/')]/@href"
)
XPATH_ALTERNATES_HREF = (
    "//*[contains(normalize-space(), 'Alternates')]/following-sibling::*[1]"
    "//a[contains(@href, '/d/companies/')]/@href"
)


def get_url_for_resolution(srcset, resolution):
    pattern = rf'([^\s]+) {resolution}'
    match = re.search(pattern, srcset)
    return match.group(1) if match else None


class TracxnDataParser:
    @staticmethod
    def extract_item(x: Selector):
        item = {}

        # Total funding
        funding = x.xpath(
            "//*[normalize-space()='Total Funding']/following-sibling::*[1]//text()").get()
        if TracxnDataParser.not_empty(funding):
            item['funding_total'] = funding.strip(" \t\n\r")

        # Website: prefer href (full URL) over text (often domain-only without scheme)
        website = x.xpath(
            "//div[@class='txn--seo-companies__detail txn--display-flex-row']//dd[@class='txn--seo-companies__details__value']//a/@href").get()
        if not TracxnDataParser.not_empty(website):
            website = x.xpath(
                "//div[@class='txn--seo-companies__detail txn--display-flex-row']//dd[@class='txn--seo-companies__details__value']//text()").get()
        if TracxnDataParser.not_empty(website):
            website = website.strip(" \t\n\r")
            item['website'] = website

        # Company name
        name = x.xpath(
            "/html/body/div[3]/div/main/div[1]/section/div/div[1]/h1//text()").get()
        if TracxnDataParser.not_empty(name):
            item['name'] = name.strip(" \t\n\r").removesuffix(
                "- Company Profile").strip(" \t\n\r")

        # Logo
        logo = x.xpath(
            "/html/body/div[3]/div/main/div[1]/section/div/a/img/@src").get()
        if TracxnDataParser.not_empty(logo):
            item['logo'] = logo.strip(" \t\n\r")

        # Description
        description = x.xpath(
            '//h3[normalize-space()="Company Details"]/following-sibling::div[1]//text()').get()
        if TracxnDataParser.not_empty(description):
            item['description'] = description.strip(" \t\n\r")

        # Acquired by
        acquired = x.xpath(
            '//*[normalize-space()="Acquired by"]/following-sibling::*[1]//text()').get()
        if TracxnDataParser.not_empty(acquired):
            item['acquired'] = acquired.strip(" \t\n\r")

        # Founded year
        founded = x.xpath(
            "//*[normalize-space()='Founded Year']/following-sibling::*[1]//text()").get()
        if TracxnDataParser.not_empty(founded):
            item['founded'] = founded.strip(" \t\n\r")

        # Industries
        industries = x.xpath(
            "//*[normalize-space()='Industries']/following-sibling::*[1]//a/text()").getall()
        item['industries'] = [industry.strip(" \t\n\r") for industry in industries]

        # Founders
        founders = x.xpath(
            "//*[normalize-space()='Founders']/following-sibling::*[1]//a/text()").getall()
        item['founders'] = [founder.strip(" \t\n\r") for founder in founders]

        return item

    @staticmethod
    def extract_similar_companies(x: Selector):
        """Extract similar/competitor company URLs (page-wide)."""
        similar_companies = x.xpath(
            '//a[contains(@href, "/d/companies/")]/@href').getall()
        result = []
        for url in similar_companies:
            if TracxnDataParser.not_empty(url) and '/d/companies/' in url:
                if not url.startswith('http'):
                    url = f'https://tracxn.com{url}'
                result.append(url)
        return result if result else None

    @staticmethod
    def _normalize_tracxn_company_url(href: str) -> str | None:
        """Turn an href into a full Tracxn company URL; return None if not a company link."""
        if not href or '/d/companies/' not in href:
            return None
        href = href.strip().split('#')[0].split('?')[0]
        if not href.startswith('http'):
            href = f'https://tracxn.com{href}' if href.startswith('/') else f'https://tracxn.com/{href}'
        return href

    @staticmethod
    def _tracxn_company_urls_from_hrefs(hrefs: list, current_page_url: str) -> list:
        """Normalize hrefs to full URLs, dedupe, and exclude current page. Returns list (maybe empty)."""
        seen = set()
        current_normalized = TracxnDataParser._normalize_tracxn_company_url(current_page_url)
        result = []
        for h in hrefs:
            url = TracxnDataParser._normalize_tracxn_company_url(h)
            if not url or url in seen or url == current_normalized:
                continue
            seen.add(url)
            result.append(url)
        return result

    @staticmethod
    def extract_competitors_and_alternates(x: Selector, current_page_url: str) -> list:
        """
        Extract Competitors and Alternates as Tracxn company URLs.

        Uses XPATH_COMPETITORS_HREF and XPATH_ALTERNATES_HREF; if those return nothing,
        falls back to page-wide extract_similar_companies. Normalizes URLs, dedupes,
        and excludes current_page_url. If the section XPaths don't match your page,
        edit XPATH_COMPETITORS_HREF and XPATH_ALTERNATES_HREF at the top of this file.
        """
        hrefs = []
        for xpath in (XPATH_COMPETITORS_HREF, XPATH_ALTERNATES_HREF):
            try:
                hrefs.extend(x.xpath(xpath).getall() or [])
            except Exception:
                pass
        if not hrefs:
            fallback = TracxnDataParser.extract_similar_companies(x)
            hrefs = list(fallback) if fallback else []
        return TracxnDataParser._tracxn_company_urls_from_hrefs(hrefs, current_page_url)

    @staticmethod
    def not_empty(data):
        if data and len(data) >= 1:
            return True
        return False
