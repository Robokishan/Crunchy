from CrunchyCrawler.extractors.baseExtract import BaseExtract
from scrapy import Selector


"""
    Section: Details
"""


class DetailsExtract(BaseExtract):
    def getTitle(self):
        return "Details"

    def getValue(self, text: list):
        item = {}
        if not text:
            return item
        for t in text:
            x = Selector(text=t)

        fields_cards = x.xpath("//tile-field").getall()
        for fields_card in fields_cards:
            fields_card = Selector(text=fields_card)
            label = fields_card.xpath("//label-with-info//text()").get()
            if label is not None:
                label = label.lstrip().rstrip().replace(" ", "")
            else:
                continue

            if "Founders" == label:
                founders_span = fields_card.xpath("//field-formatter//span")
                founders = []

                for span in founders_span:
                    a_tags = span.xpath(".//a")

                    for a_tag in a_tags:
                        text = a_tag.xpath("@title").get()
                        founders.append(text)

                    item["founders"] = founders

            # TODO: fix xpath for the stock symbol
            if "Stock" == label:
                item["stock_symbol"] = (
                    fields_card.xpath("//field-formatter//text()")
                    .get()
                    .lstrip()
                    .rstrip()
                    .replace(" ", "")
                )

        return item
