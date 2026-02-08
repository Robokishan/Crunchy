from CrunchyCrawler.extractors.baseExtract import BaseExtract
from scrapy import Selector

'''
    Section: About
'''


class CompanyDetails(BaseExtract):

    def getTitle(self):
        return "Company Details"

    def getValue(self, text: list):
        item = {}
        for t in text:
            x = Selector(text=t)
            title = x.xpath('//h3/text()').get()
            if title == self.getTitle():
                item['description'] = x.xpath(
                    '//*[@id="about-the-company"]').get()
                fields_cards = x.xpath('//fields-card').getall()
                for fields_card in fields_cards:
                    fields_card = Selector(text=fields_card)
                    labels = fields_card.xpath('//label-with-info').getall()
                    for label in labels:
                        label = Selector(text=label)
                        if "Acquired" in label.xpath('//text()').get():
                            item['acquired'] = fields_card.xpath(
                                '//field-formatter//text()').get().lstrip().rstrip().replace(' ', '')
                return item
        return None


'''
    Section: Highlights
'''


class HighlightsExtract(BaseExtract):

    def getTitle(self):
        return "Highlights"

    def getValue(self, text: list):
        item = {}
        for t in text:
            x = Selector(text=t)
            title = x.xpath('//h2/text()').get()
            if title == self.getTitle():
                fields_cards = x.xpath('//anchored-values/div').getall()
                for fields_card in fields_cards:
                    fields_card = Selector(text=fields_card)
                    labels = fields_card.xpath('//label-with-info').getall()
                    for label in labels:
                        label = Selector(text=label)
                        label = label.xpath(
                            '//text()').get().lstrip().rstrip().replace(' ', '')
                        if "TotalFunding" == label:
                            try:
                                item['funding'] = fields_card.xpath(
                                    '//field-formatter//text()').get().lstrip().rstrip().replace(' ', '')
                            except Exception as e:
                                pass
                return item
        return None


'''
    Section: Details
'''


class DetailsExtract(BaseExtract):

    def getTitle(self):
        return "Details"

    def getValue(self, text: list):
        item = {}
        for t in text:
            x = Selector(text=t)
            title = x.xpath('//h2/text()').get()
            if title == self.getTitle():
                item['long_description'] = x.xpath(
                    '//description-card//text()').get()
                fields_cards = x.xpath('//fields-card/ul/li').getall()
                for fields_card in fields_cards:
                    fields_card = Selector(text=fields_card)
                    labels = fields_card.xpath('//label-with-info').getall()

                    for label in labels:

                        label = Selector(text=label)
                        label = label.xpath(
                            '//text()').get().lstrip().rstrip().replace(' ', '')
                        if "Founded" == label:
                            item['founded'] = fields_card.xpath(
                                '//field-formatter//text()').get().lstrip().rstrip().replace(' ', '')

                        if "Industries" == label:
                            item['industries'] = fields_card.xpath(
                                '//field-formatter//text()').getall()

                        if "Founders" == label:
                            founders_span = fields_card.xpath(
                                '//field-formatter//identifier-multi-formatter')
                            founders = []

                            for span in founders_span:
                                a_tags = span.xpath('.//a')
                                for a_tag in a_tags:
                                    text = a_tag.xpath(
                                        'normalize-space()').get()
                                    # href = a_tag.xpath('@href').get()
                                    founders.append(text)

                                item['founders'] = founders

                        if "LastFunding" == label:
                            item['lastfunding'] = fields_card.xpath(
                                '//field-formatter//text()').get()

                        if "Stock" == label:
                            item['stock_symbol'] = fields_card.xpath(
                                '//field-formatter//text()').get().lstrip().rstrip().replace(' ', '')

                return item
        return None
