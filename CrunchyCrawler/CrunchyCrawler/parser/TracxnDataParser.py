"""
TracxnDataParser - Parses company data from Tracxn company pages.

Tracxn URL pattern: https://tracxn.com/d/companies/<slug>/__<hash>#about-the-company

This parser extracts:
- Company name, website, description, logo
- Funding total
- Founders
- Founded date, industries
"""

from scrapy.selector import Selector
from CrunchyCrawler.extractors.tracxnExtractor import DetailsExtract
from CrunchyCrawler.extractors.tracxnExtractor import CompanyDetails
from CrunchyCrawler.extractors.tracxnExtractor import HighlightsExtract
import regex as re

# list of all extractors add if any new extractor come for tracxn
extractors = [CompanyDetails, DetailsExtract, HighlightsExtract]


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
        """Extract similar/competitor company URLs."""
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
    def not_empty(data):
        if data and len(data) >= 1:
            return True
        return False
