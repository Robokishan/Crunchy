from scrapy.selector import Selector
from CrunchyCrawler.request import generateRequest
from CrunchyCrawler.rabbitmq.spiders import RabbitMQMixin
from CrunchyCrawler.parser.CrunchbaseDataParser import CrunchbaseDataParser
from scrapy.linkextractors import LinkExtractor
from loguru import logger

class CrunchySpider(RabbitMQMixin):
    name = "crunchy"

    async def parse(self, response):
        x = Selector(response)
        item = CrunchbaseDataParser.extract_item(x)

        item['crunchbase_url'] = response.url
        delivery_tag = response.meta.get('delivery_tag')
        item['delivery_tag'] = response.meta.get('delivery_tag')
        item['queue'] = response.meta.get('queue')
        queue = response.meta.get('queue')
        item['_response'] = response.status
        
        logger.info(f"Scrapped item ----> {item}")
        
        similarCompanies = CrunchbaseDataParser.extractSimilarCompanies(x)
        if similarCompanies:
            similarCompanies = response.urljoin(similarCompanies)
            logger.info(f"Getting similarCompanies-------> {similarCompanies}")
            yield generateRequest(similarCompanies, delivery_tag, callback=self.parseSimilarCompanies, previousResult=item, queue=queue)
        else:
            yield item

    async def parseSimilarCompanies(self, response):
        # parse similar companies from response
        link_ext = LinkExtractor(
            restrict_xpaths="//org-similarity-card", allow=r'\b\/organization\b')
        links = link_ext.extract_links(response)
        item = {}
        item['similar_companies'] = []
        previous_results = response.meta.get('previousResult', {})
        logger.info(f"Similar company links --> {links}")
        for link in links:
            item['similar_companies'].append(link.url)
        current_results = dict(item)
        combined_results = {**previous_results, **current_results}
        yield combined_results
