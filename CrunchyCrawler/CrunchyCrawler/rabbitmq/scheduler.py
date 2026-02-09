from .connection import get_channels, get_internal_channel, close
from scrapy.utils.misc import load_object
from loguru import logger


# default values
SCHEDULER_PERSIST = True
QUEUE_KEY = "%(spider)s:requests"
SPIDER_QUEUE_CLASS = "CrunchyCrawler.rabbitmq.queue.SpiderQueue"
CRAWL_QUEUE_CLASS = "CrunchyCrawler.rabbitmq.queue.CrawlQueue"
DUPEFILTER_KEY = "%(spider)s:dupefilter"
IDLE_BEFORE_CLOSE = 0


class Scheduler(object):
    """RabbitMQ Scheduler for Scrapy. Consumes from spider queue, then Tracxn crawl queue, then Crunchbase crawl queue."""

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
    }

    def __init__(
        self,
        internal_channel,
        cb_channel,
        tracxn_channel,
        persist,
        spider_queue_key,
        spider_queue_cls,
        cb_crawl_queue_key,
        tracxn_crawl_queue_key,
        crawl_queue_cls,
        dupefilter_key,
        idle_before_close,
        *args,
        **kwargs,
    ):
        self.internal_channel = internal_channel
        self.cb_channel = cb_channel
        self.tracxn_channel = tracxn_channel
        self.persist = persist
        self.spider_queue_key = spider_queue_key
        self.cb_crawl_queue_key = cb_crawl_queue_key
        self.tracxn_crawl_queue_key = tracxn_crawl_queue_key
        self.queue_cls = spider_queue_cls
        self.crawl_queue_cls = crawl_queue_cls
        self.dupefilter_key = dupefilter_key
        self.idle_before_close = idle_before_close
        self.stats = None
        self.counter = 0
        self.threshold = 60
        logger.debug("Using custom scheduler")

    def __len__(self):
        return len(self.queue)

    @classmethod
    def from_settings(cls, settings):
        persist = settings.get("SCHEDULER_PERSIST", SCHEDULER_PERSIST)
        spider_queue_key = settings.get("SCHEDULER_QUEUE_KEY", QUEUE_KEY)
        spider_queue_cls = load_object(
            settings.get("SCHEDULER_QUEUE_CLASS", SPIDER_QUEUE_CLASS)
        )
        crawl_queue_cls = load_object(
            settings.get("SCHEDULER_CRAWL_QUEUE_CLASS", CRAWL_QUEUE_CLASS)
        )

        cb_crawl_queue_key = settings.get("RB_CRUNCHBASE_CRAWL_QUEUE")
        tracxn_crawl_queue_key = settings.get("RB_TRACXN_CRAWL_QUEUE")
        crunchy_crawl_queue = settings.get("CRUNCHY_CRAWL_QUEUE")
        if crunchy_crawl_queue == "crunchbase":
            tracxn_crawl_queue_key = None
        elif crunchy_crawl_queue == "tracxn":
            cb_crawl_queue_key = None

        dupefilter_key = settings.get("DUPEFILTER_KEY", DUPEFILTER_KEY)
        idle_before_close = settings.get(
            "SCHEDULER_IDLE_BEFORE_CLOSE", IDLE_BEFORE_CLOSE
        )
        cb_channel, tracxn_channel = get_channels()
        internal_channel = get_internal_channel()
        return cls(
            internal_channel,
            cb_channel,
            tracxn_channel,
            persist,
            spider_queue_key,
            spider_queue_cls,
            cb_crawl_queue_key,
            tracxn_crawl_queue_key,
            crawl_queue_cls,
            dupefilter_key,
            idle_before_close,
        )

    @classmethod
    def from_crawler(cls, crawler):
        instance = cls.from_settings(crawler.settings)
        instance.stats = crawler.stats
        return instance

    def open(self, spider):
        self.spider = spider

        self.queue = self.queue_cls(
            self.internal_channel, spider, self.spider_queue_key
        )
        self.cb_crawl_queue = self.crawl_queue_cls(
            self.cb_channel, spider, self.cb_crawl_queue_key, meta_label="crunchbase"
        )
        self.tracxn_crawl_queue = self.crawl_queue_cls(
            self.tracxn_channel,
            spider,
            self.tracxn_crawl_queue_key,
            meta_label="tracxn",
        )

        if self.idle_before_close < 0:
            self.idle_before_close = 0

        if len(self.queue):
            spider.log("Resuming crawl (%d requests scheduled)" % len(self.queue))

    def close(self, reason):
        close(self.cb_channel)
        close(self.tracxn_channel)

    def enqueue_request(self, request):
        # if not request.dont_filter and self.df.request_seen(request):
        #     return
        if self.stats:
            self.stats.inc_value("scheduler/enqueued/rabbitmq", spider=self.spider)
        self.queue.push(request)

    def next_request(self):
        logger.debug("Getting new request")
        request = self.queue.pop()
        logger.info("From Spider queue {} live:{}", request, self.cb_channel.is_open)
        logger.info(
            "Counter---->>> Counter:{} Threshold:{}", self.counter, self.threshold
        )
        if request is None and self.counter >= self.threshold:
            if self.tracxn_crawl_queue.key is not None:
                request = self.tracxn_crawl_queue.pop()
                logger.info(
                    "From Tracxn crawl queue: {} live:{}",
                    request,
                    self.tracxn_channel.is_open,
                )
            if request is None and self.cb_crawl_queue.key is not None:
                request = self.cb_crawl_queue.pop()
                logger.info(
                    "From Crunchbase crawl queue: {} live:{}",
                    request,
                    self.cb_channel.is_open,
                )
            if request is not None:
                self.counter = 0
        logger.info("request --->>>> {}", request)
        self.counter += 1
        return request

    def has_pending_requests(self):
        """
        We never want to say we have pending requests
        If this returns True scrapy sometimes hangs.
        """
        return False
