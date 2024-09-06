from scrapy.selector import Selector
from CrunchyCrawler.extractors.extractors import DetailsExtract
from CrunchyCrawler.extractors.extractors import AboutExtract
from CrunchyCrawler.extractors.extractors import HighlightsExtract
import regex as re

# list of all exctractors add if any new extractor come for crunchbase
extractors = [AboutExtract, DetailsExtract, HighlightsExtract]

def get_url_for_resolution(srcset, resolution):
    pattern = rf'([^\s]+) {resolution}'
    match = re.search(pattern, srcset)
    return match.group(1) if match else None

class CrunchbaseDataParser:
    @staticmethod
    def extract_item(x: Selector):
        item = {}

        # old extractors remove these and add new extractors class
        funding = x.xpath(
            "//span[contains(@class, 'field-type-money')]/text()").get()
        if CrunchbaseDataParser.not_empty(funding):
            item['funding'] = funding.strip(" \t\n\r")

        website = x.xpath(
            "//span[1]/field-formatter[1]/link-formatter[1]/a[1]/@href").get()
        if CrunchbaseDataParser.not_empty(website):
            item['website'] = website

        name = x.xpath("//h1[1]/text()").get()
        if CrunchbaseDataParser.not_empty(name):
            item['name'] = name.strip(" \t\n\r")
        
        logo = x.xpath("//profile-header-logo[1]/picture[1]/source[1]/@srcset").get()
        if logo is not None:
            logo = get_url_for_resolution(logo, '1x')
        if CrunchbaseDataParser.not_empty(logo):
            item['logo'] = logo.strip(" \t\n\r")

        # get all the exctractor and exctract information
        profile_section = x.xpath('//profile-section').getall()
        for e in extractors:
            val = e().getValue(text=profile_section)
            if val:
                item.update(val)

        return item

    def extractSimilarCompanies(x: Selector):
        similar_companies = x.xpath(
            '//a[contains(@href, "similarity")]/@href').get()
        if CrunchbaseDataParser.not_empty(similar_companies):
            return similar_companies
        return None

    @staticmethod
    def not_empty(data):
        if data and len(data) >= 1:
            return True
        return False
