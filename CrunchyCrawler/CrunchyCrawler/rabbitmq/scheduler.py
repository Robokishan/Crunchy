
from .connection import from_settings, close
from scrapy import Request
from scrapy.utils.misc import load_object
from .dupefilter import RFPDupeFilter
from scrapy_playwright.page import PageMethod


# default values
SCHEDULER_PERSIST = True
QUEUE_KEY = '%(spider)s:requests'
SPIDER_QUEUE_CLASS = 'CrunchyCrawler.rabbitmq.queue.SpiderQueue'
MAIN_QUEUE_CLASS = 'CrunchyCrawler.rabbitmq.queue.MainQueue'
DUPEFILTER_KEY = '%(spider)s:dupefilter'
IDLE_BEFORE_CLOSE = 0


class Scheduler(object):
    """ A RabbitMQ Scheduler for Scrapy.
    """

    # default headers
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9',  # this is game changing header
    }

    def __init__(self, server, persist, spider_queue_key, spider_queue_cls, main_queue_key, main_queue_cls, dupefilter_key, idle_before_close, *args, **kwargs):
        self.server = server
        # TODO: don't know use of persist
        self.persist = persist
        self.spider_queue_key = spider_queue_key
        self.main_queue_key = main_queue_key
        self.queue_cls = spider_queue_cls
        self.main_queue_cls = main_queue_cls
        self.dupefilter_key = dupefilter_key
        self.idle_before_close = idle_before_close
        self.stats = None
        self.counter = 20
        self.threshold = 20
        print("Using custom scheduler")

    def __len__(self):
        return len(self.queue)

    @classmethod
    def from_settings(cls, settings):
        persist = settings.get('SCHEDULER_PERSIST', SCHEDULER_PERSIST)
        spider_queue_key = settings.get('SCHEDULER_QUEUE_KEY', QUEUE_KEY)
        spider_queue_cls = load_object(settings.get(
            'SCHEDULER_QUEUE_CLASS', SPIDER_QUEUE_CLASS))

        main_queue_key = settings.get('RB_MAIN_QUEUE')
        main_queue_cls = load_object(settings.get(
            'SCHEDULER_MAIN_QUEUE_CLASS', MAIN_QUEUE_CLASS))

        dupefilter_key = settings.get('DUPEFILTER_KEY', DUPEFILTER_KEY)
        idle_before_close = settings.get(
            'SCHEDULER_IDLE_BEFORE_CLOSE', IDLE_BEFORE_CLOSE)
        server = from_settings()
        return cls(server, persist, spider_queue_key, spider_queue_cls, main_queue_key, main_queue_cls, dupefilter_key, idle_before_close)

    @classmethod
    def from_crawler(cls, crawler):
        instance = cls.from_settings(crawler.settings)
        instance.stats = crawler.stats
        return instance

    def open(self, spider):
        self.spider = spider
        self.queue = self.queue_cls(self.server, spider, self.spider_queue_key)
        self.main_queue = self.main_queue_cls(
            self.server, spider, self.main_queue_key)
        # self.df = RFPDupeFilter(self.server, self.dupefilter_key % {
        # 'spider': spider.name})

        if self.idle_before_close < 0:
            self.idle_before_close = 0

        if len(self.queue):
            spider.log("Resuming crawl (%d requests scheduled)" %
                       len(self.queue))

    def close(self, reason):
        close(self.server)
        # if not self.persist:
        #     # self.df.clear()
        #     self.queue.clear()
        #     self.main_queue.clear()

    def enqueue_request(self, request):
        # if not request.dont_filter and self.df.request_seen(request):
        #     return
        if self.stats:
            self.stats.inc_value(
                'scheduler/enqueued/rabbitmq', spider=self.spider)
        self.queue.push(request)

    def next_request(self):

        print("Getting new request")

        block_pop_timeout = self.idle_before_close
        request = self.queue.pop()
        print("From Spider queue", request)
        print("Counter---->>>", self.counter)
        if request == None:
            if self.counter >= self.threshold:
                request = self.main_queue.pop()
                print("From Main queue", request)
                if request != None:
                    self.counter = 0
        print("request --->>>>", request)
        # self.stats.inc_value(
        #     'scheduler/dequeued/rabbitmq', spider=self.spider)
        self.counter += 1
        return request

    def has_pending_requests(self):
        '''
        We never want to say we have pending requests
        If this returns True scrapy sometimes hangs.
        '''
        return False
