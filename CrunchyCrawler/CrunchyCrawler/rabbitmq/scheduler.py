
from .connection import get_channels, get_internal_channel,  close
from scrapy import Request
from scrapy.utils.misc import load_object
from .dupefilter import RFPDupeFilter
from scrapy_playwright.page import PageMethod


# default values
SCHEDULER_PERSIST = True
QUEUE_KEY = '%(spider)s:requests'
SPIDER_QUEUE_CLASS = 'CrunchyCrawler.rabbitmq.queue.SpiderQueue'
MAIN_QUEUE_CLASS = 'CrunchyCrawler.rabbitmq.queue.MainQueue'
PRIORITY_QUEUE_CLASS = 'CrunchyCrawler.rabbitmq.queue.PriorityQueue'
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

    def __init__(self, internal_channel, main_channel, priority_channel, persist, spider_queue_key, spider_queue_cls, main_queue_key, main_queue_cls, priority_queue_key, priority_queue_cls, dupefilter_key, idle_before_close, *args, **kwargs):
        self.internal_channel = internal_channel
        self.main_channel = main_channel
        self.priority_channel = priority_channel
        self.persist = persist
        self.spider_queue_key = spider_queue_key
        self.main_queue_key = main_queue_key
        self.queue_cls = spider_queue_cls
        self.main_queue_cls = main_queue_cls
        self.priority_queue_cls = priority_queue_cls
        self.priority_queue_key = priority_queue_key
        self.dupefilter_key = dupefilter_key
        self.idle_before_close = idle_before_close
        self.stats = None
        self.counter = 0
        self.threshold = 60
        print("Using custom scheduler")

    def __len__(self):
        return len(self.internal_queue)

    @classmethod
    def from_settings(cls, settings):
        persist = settings.get('SCHEDULER_PERSIST', SCHEDULER_PERSIST)
        spider_queue_key = settings.get('SCHEDULER_QUEUE_KEY', QUEUE_KEY)
        spider_queue_cls = load_object(settings.get(
            'SCHEDULER_QUEUE_CLASS', SPIDER_QUEUE_CLASS))

        main_queue_key = settings.get('RB_MAIN_QUEUE')
        main_queue_cls = load_object(settings.get(
            'SCHEDULER_MAIN_QUEUE_CLASS', MAIN_QUEUE_CLASS))
        
        priority_queue_key = settings.get('RABBIT_MQ_PRIORITY_QUEUE')
        priority_queue_cls = load_object(settings.get(
            'SCHEDULER_PRIORITY_QUEUE_CLASS', PRIORITY_QUEUE_CLASS))
        

        dupefilter_key = settings.get('DUPEFILTER_KEY', DUPEFILTER_KEY)
        idle_before_close = settings.get(
            'SCHEDULER_IDLE_BEFORE_CLOSE', IDLE_BEFORE_CLOSE)
        main_channel, priority_channel = get_channels()
        internal_channel = get_internal_channel()
        return cls(internal_channel, main_channel, priority_channel, persist, spider_queue_key, spider_queue_cls, main_queue_key, main_queue_cls, priority_queue_key, priority_queue_cls, dupefilter_key, idle_before_close)

    @classmethod
    def from_crawler(cls, crawler):
        instance = cls.from_settings(crawler.settings)
        instance.stats = crawler.stats
        return instance

    def open(self, spider):
        self.spider = spider

        self.internal_queue = self.queue_cls(self.internal_channel, spider, self.spider_queue_key)
        self.main_queue = self.main_queue_cls(
            self.main_channel, spider, self.main_queue_key)
        self.priority_queue = self.priority_queue_cls(
            self.priority_channel, spider, self.priority_queue_key)
        
        # self.df = RFPDupeFilter(self.server, self.dupefilter_key % {
        # 'spider': spider.name})

        if self.idle_before_close < 0:
            self.idle_before_close = 0

        if len(self.internal_queue):
            spider.log("Resuming crawl (%d requests scheduled)" %
                       len(self.internal_queue))

    def close(self, reason):
        close(self.main_channel)
        close(self.priority_channel)
        close(self.internal_channel)
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
        self.internal_queue.push(request)

    def next_request(self):

        print("Getting new request")

        block_pop_timeout = self.idle_before_close
        request = self.internal_queue.pop()
        print("From Spider queue", request, self.internal_channel.is_open)
        print("Counter---->>>", self.counter, self.threshold)
        if request == None:
            if self.counter >= self.threshold:
                # after threshold is passed check for priority queue
                # check if priority channel is connected if not throw error
                request = self.priority_queue.pop()
                print("From Priority queue", request, self.priority_channel.is_open)

                # if priority queue is also empty then check main queue
                if request == None:
                    request = self.main_queue.pop()
                    print("From Main queue", request, self.main_channel.is_open)
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
