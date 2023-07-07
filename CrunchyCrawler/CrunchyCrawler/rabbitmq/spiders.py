from scrapy import Spider
from scrapy import signals
from scrapy.exceptions import DontCloseSpider

from CrunchyCrawler.rabbitmq.connection import from_settings
from scrapy import Request
from scrapy_playwright.page import PageMethod


class RabbitMQMixin(Spider):
    def _set_crawler(self, crawler):
        super(RabbitMQMixin, self)._set_crawler(crawler)
        self.crawler.signals.connect(self.spider_idle,
                                     signal=signals.spider_idle)
        self.crawler.signals.connect(self.item_error,
                                     signal=signals.item_error)
        self.crawler.signals.connect(self.item_dropped,
                                     signal=signals.item_dropped)
        self.crawler.signals.connect(self.spider_error,
                                     signal=signals.spider_error)
        # self.crawler.signals.connect(self.item_error,
        #                              signal=signals.item_passed)
        # self.crawler.signals.connect(self.item_error,
        #                              signal=signals.item_scraped)
        self.server = from_settings()

    def request(self, url, callback, previousResult):
        return Request(url,
                       headers=self.headers,
                       errback=self.errback,
                       callback=callback,
                       meta={
                           "previousResult": previousResult,
                           "playwright": True,
                           #    "playwright_include_page": True,
                           "playwright_page_methods": [
                               PageMethod(
                                   "wait_for_selector", ".profile-name")
                           ],
                       })

    def errback(self, failure):
        print("Failure of similar companies", failure)
        try:
            request = failure.request
            delivery_tag = request.meta.get('delivery_tag')
            print("Spider Delivery tag", delivery_tag)
            self.server.basic_nack(delivery_tag=delivery_tag, requeue=True)
        except Exception as e:
            print("Spider Rabbitmq other error something went wrong", e)

    def spider_error(self, failure, response, spider):
        print("Spider error ---> ", failure, response, spider)

    def spider_idle(self):
        print("Sitting idle")
        raise DontCloseSpider

    async def item_error(self, item, response, failure):
        print("item_error -->", item, failure)
        # page = response.meta["playwright_page"]
        # await page.close()

    async def item_dropped(self, item, response, failure):
        print("item_dropped -->", item, failure)
        # page = response.meta["playwright_page"]
        # await page.close()
