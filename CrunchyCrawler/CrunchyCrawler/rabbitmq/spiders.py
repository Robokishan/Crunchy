from scrapy import Spider
from scrapy import signals
from scrapy.exceptions import DontCloseSpider

from CrunchyCrawler.rabbitmq.connection import get_channels


class RabbitMQMixin(Spider):
    def _set_crawler(self, crawler):
        super(RabbitMQMixin, self)._set_crawler(crawler)
        self.crawler.signals.connect(self.spider_idle,
                                     signal=signals.spider_idle)

    def spider_idle(self):
        print("Sitting idle")
        raise DontCloseSpider

