from scrapy.selector import Selector
from CrunchyCrawler.extractors.extractors import DetailsExtract
from CrunchyCrawler.extractors.extractors import AboutExtract
from CrunchyCrawler.extractors.extractors import HighlightsExtract

# list of all exctractors add if any new extractor come for crunchbase
extractors = [AboutExtract, DetailsExtract, HighlightsExtract]


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

        logo = x.xpath("//profile-header-logo[1]/picture[1]/img[1]").get()
        if CrunchbaseDataParser.not_empty(logo):
            item['logo'] = logo.strip(" \t\n\r")

        name = x.xpath("//h1[1]/text()").get()
        if CrunchbaseDataParser.not_empty(name):
            item['name'] = name.strip(" \t\n\r")

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
