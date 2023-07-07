from scrapy.selector import Selector
from scrapy import Spider
from CrunchyCrawler.parser.CrunchbaseDataParser import CrunchbaseDataParser
from scrapy.linkextractors import LinkExtractor
from scrapy import Request
from scrapy_playwright.page import PageMethod


class CrunchySpider(Spider):
    name = "testcrunchy"

    # default headers
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9',  # this is game changing header
    }

    crunchbase_page = "https://crunchbase.com/organization/browserstack"
    # crunchbase_page = "https://www.crunchbase.com/organization/cnvrg-io"
    crunchbase_page = "https://www.crunchbase.com/organization/greaves-cotton-ltd"
    # crunchbase_page = "https://crunchbasess.free.beeceptor.com/organization/level-ai"

    def firstrequest(self, url, callback):
        return Request(url, callback=callback,
                       headers=self.headers,
                       meta={
                           # this is just a default ip address It will be changed in middleware
                           #   "playwright_context_kwargs": {
                           #       "proxy": {
                           #           "server": "http://147.135.54.182:3128",
                           #       },
                           #   },
                           "playwright": True,
                           "playwright_include_page": True,
                           "playwright_page_methods": [
                               PageMethod(
                                   "wait_for_load_state", "networkidle")
                           ],
                       })

    def start_requests(self):
        yield self.firstrequest(self.crunchbase_page, self.parse)

    def request(self, url, callback, previousResult):
        return Request(url,
                       headers=self.headers,
                       callback=callback,
                       meta={
                           # this is just a default ip address It will be changed in middleware
                           #   "playwright_context_kwargs": {
                           #       "proxy": {
                           #           "server": "http://147.135.54.182:3128",
                           #       },
                           #   },
                           "previousResult": previousResult,
                           "playwright": True,
                           "playwright_include_page": True,
                           "playwright_page_methods": [
                               PageMethod(
                                   "wait_for_load_state", "networkidle")
                           ],
                       })

    async def parse(self, response):
        page = response.meta["playwright_page"]
        await page.close()
        # interactive shell for scrapy response debugging
        from scrapy.shell import inspect_response
        inspect_response(response, self)
        # rest of the parsing
        x = Selector(response)
        item = CrunchbaseDataParser.extract_item(x)
        item['crunchbase_url'] = response.url
        print(item)
        yield item
        # similarCompanies = CrunchbaseDataParser.extractSimilarCompanies(x)
        # if similarCompanies:
        #     # similarCompanies = "/hello"
        #     similarCompanies = response.urljoin(similarCompanies)
        #     print("Getting similarCompanies------->", similarCompanies)
        #     yield self.request(similarCompanies, self.parseSimilarCompanies, item)

    def parseSimilarCompanies(self, response):
        # parse similar companies from response
        link_ext = LinkExtractor(
            restrict_xpaths="//org-similarity-card", allow=r'\b\/organization\b')
        links = link_ext.extract_links(response)
        item = {}
        item['similar_companies'] = []
        previous_results = response.meta.get('previousResult', {})
        print(links)
        for link in links:
            item['similar_companies'].append(link.url)
        current_results = dict(item)
        combined_results = {**previous_results, **current_results}
        yield combined_results

        # interactive shell for scrapy response debugging
        # from scrapy.shell import inspect_response
        # inspect_response(response, self)
