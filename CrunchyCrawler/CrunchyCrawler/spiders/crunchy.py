from scrapy.selector import Selector
from CrunchyCrawler.rabbitmq.spiders import RabbitMQMixin
from CrunchyCrawler.parser.CrunchbaseDataParser import CrunchbaseDataParser
from scrapy.linkextractors import LinkExtractor


class CrunchySpider(RabbitMQMixin):
    name = "crunchy"

    # default headers
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9',  # this is game changing header
    }

    async def parse(self, response):
        # page = response.meta["playwright_page"]
        # await page.close()

        print("Parsing Done")

        # rest of the parsing
        x = Selector(response)
        item = CrunchbaseDataParser.extract_item(x)
        item['crunchbase_url'] = response.url
        item['delivery_tag'] = response.meta.get('delivery_tag')
        item['_response'] = response.status
        print("Scrapped item ---->", item)
        similarCompanies = CrunchbaseDataParser.extractSimilarCompanies(x)
        if similarCompanies:
            # similarCompanies = "/hello"
            similarCompanies = response.urljoin(similarCompanies)
            print("Getting similarCompanies------->", similarCompanies)
            yield self.request(similarCompanies, self.parseSimilarCompanies, item)
        else:
            yield item

    async def parseSimilarCompanies(self, response):
        # page = response.meta["playwright_page"]
        # await page.close()
        # parse similar companies from response
        link_ext = LinkExtractor(
            restrict_xpaths="//org-similarity-card", allow=r'\b\/organization\b')
        links = link_ext.extract_links(response)
        item = {}
        item['similar_companies'] = []
        previous_results = response.meta.get('previousResult', {})
        print("Similar company links --> ", links)
        for link in links:
            item['similar_companies'].append(link.url)
        current_results = dict(item)
        combined_results = {**previous_results, **current_results}
        yield combined_results
