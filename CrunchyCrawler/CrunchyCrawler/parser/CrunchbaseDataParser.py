from re import A
from scrapy.selector import Selector
from CrunchyCrawler.extractors.extractors import DetailsExtract
import regex as re

# list of all exctractors add if any new extractor come for crunchbase
extractors = [DetailsExtract]


def get_url_for_resolution(srcset, resolution):
    pattern = rf"([^\s]+) {resolution}"
    match = re.search(pattern, srcset)
    return match.group(1) if match else None


class CrunchbaseDataParser:
    @staticmethod
    def extract_item(x: Selector):
        item = {}

        # old extractors remove these and add new extractors class
        funding = x.xpath("//span[contains(@class, 'field-type-money')]/text()").get()
        if CrunchbaseDataParser.not_empty(funding):
            item["funding"] = funding.strip(" \t\n\r")

        website = x.xpath(
            "//span[1]/field-formatter[1]/link-formatter[1]/a[1]/@href"
        ).get()
        if CrunchbaseDataParser.not_empty(website):
            item["website"] = website

        name = x.xpath("//span[@class='entity-name']//text()").get()
        if CrunchbaseDataParser.not_empty(name):
            item["name"] = name.strip(" \t\n\r")

        logo = x.xpath(
            "//div[@class='identifier-image-container']//picture/source/@srcset"
        ).get()
        if logo is not None:
            logo = get_url_for_resolution(logo, "1x")
        if CrunchbaseDataParser.not_empty(logo):
            item["logo"] = logo.strip(" \t\n\r")

        # get all the exctractor and exctract information
        industries = x.xpath("//div[@class='categories']//text()").getall()
        if CrunchbaseDataParser.not_empty(industries):
            item["industries"] = [industry.strip(" \t\n\r") for industry in industries]

        description = x.xpath(
            "//profile-v3-header//span[contains(@class,'expanded-only-content')]//text()"
        ).getall()
        if CrunchbaseDataParser.not_empty(description):
            item["description"] = " ".join(d.strip(" \t\n\r") for d in description)

        long_description = x.xpath(
            "//overview-details//tile-description//div//span//text()"
        ).getall()
        print("long_description: ", long_description)
        if CrunchbaseDataParser.not_empty(long_description):
            item["long_description"] = " ".join(
                d.strip(" \t\n\r") for d in long_description
            )
        acquired = x.xpath(
            "//profile-v3-header//label-with-icon[@iconkey='icon_acquisition']//identifier-formatter//div[@class='identifier-label']//text()"
        ).get()
        if CrunchbaseDataParser.not_empty(acquired):
            item["acquired"] = acquired.strip(" \t\n\r")

        lastfunding = x.xpath(
            "//profile-v3-header//label-with-icon[@iconkey='icon_company']//field-formatter//text()"
        ).get()
        if CrunchbaseDataParser.not_empty(lastfunding):
            item["lastfunding"] = lastfunding.strip(" \t\n\r")

        details_section = x.xpath("//overview-details").getall()
        val = DetailsExtract().getValue(text=details_section)
        print("val: details", val)
        if val is not None:
            print("val: details", val)
            item.update(val)

        return item

    @staticmethod
    def not_empty(data):
        if data and len(data) >= 1:
            return True
        return False
