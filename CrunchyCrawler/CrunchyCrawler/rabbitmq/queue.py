from scrapy.utils.request import request_from_dict
import pickle
import json
from scrapy import Request
from scrapy_playwright.page import PageMethod
from loguru import logger
from CrunchyCrawler.request import generateRequest


class Base(object):

    def __init__(self, server, spider, key, exchange=None):
        """Initialize per-spider RabbitMQ queue.
        Parameters:
            server -- rabbitmq connection
            spider -- spider instance
            key -- key for this queue (e.g. "%(spider)s:queue")
        """
        self.server = server
        self.spider = spider
        self.key = key % {'spider': spider.name}
        logger.debug(f"starting here --> {key % {'spider': spider.name}}" )
        self._declare_queue()

    def _declare_queue(self):
        pass

    def _encode_request(self, request: Request):
        """Encode a request object"""
        return pickle.dumps(request.to_dict(spider=self.spider))

    def _decode_request(self, encoded_request):
        """Decode an request previously encoded"""
        return request_from_dict(pickle.loads(encoded_request), spider=self.spider)

    def __len__(self):
        """Return the length of the queue"""
        raise NotImplementedError

    def push(self, request):
        """Push a request"""
        raise NotImplementedError

    def pop(self, timeout=0):
        """Pop a request"""
        raise NotImplementedError

    def clear(self):
        """Clear queue/stack"""
        self.server.queue_purge(self.key)


class SpiderQueue(Base):

    def _declare_queue(self):
        logger.debug(f"Declaring queue: {self.key}")
        self.server.queue_declare(self.key)

    def __len__(self):
        """Return the length of the queue"""
        response = self.server.queue_declare(self.key, passive=True)
        return response.method.message_count

    def push(self, request):
        self.server.basic_publish(
            exchange='',
            routing_key=self.key,
            body=self._encode_request(request)
        )

    def pop(self):
        method_frame, header, body = self.server.basic_get(queue=self.key)
        if body != None:
            logger.info(f"SpiderQ Sent ack: {method_frame.delivery_tag}")
            self.server.basic_ack(delivery_tag=method_frame.delivery_tag)
            return self._decode_request(body)


def _parse_crawl_message(body: str):
    """Parse crawl queue message: JSON {"url": ..., "entry_point": ...} or plain URL. Returns (url, entry_point)."""
    body = (body or "").strip()
    if not body:
        return "", None
    if body.startswith("{") and "url" in body:
        try:
            data = json.loads(body)
            url = data.get("url", "")
            entry_point = data.get("entry_point")
            return url or "", entry_point
        except (json.JSONDecodeError, TypeError):
            pass
    return body, None


def _is_crunchbase_url(url):
    """True iff URL is clearly a Crunchbase URL."""
    return bool(url and "crunchbase.com" in url)


def _is_tracxn_url(url):
    """True iff URL is clearly a Tracxn URL."""
    return bool(url and "tracxn.com" in url)


class CrawlQueue:
    """Single crawl queue (Crunchbase or Tracxn). Consumes from one RabbitMQ queue; validates URL matches queue type."""

    def __init__(self, server, spider, key=None, meta_label="crunchbase", exchange=None):
        """
        Args:
            server: RabbitMQ channel
            spider: spider instance
            key: RabbitMQ queue name (e.g. crawl_crunchbase_queue)
            meta_label: 'crunchbase' or 'tracxn' (for request meta and URL validation)
        """
        self.server = server
        self.spider = spider
        self.key = key
        self.meta_label = meta_label
        logger.debug("Crawl queue: {} ({})", self.key, meta_label)

    def __len__(self):
        if self.key is None:
            return 0
        response = self.server.queue_declare(self.key, passive=True)
        return response.method.message_count

    def push(self, request):
        pass

    def pop(self):
        if self.key is None:
            return None
        method_frame, header, body = self.server.basic_get(queue=self.key)
        if body is None:
            return None
        encoded = body.decode("utf-8")
        request = self._decode_request(encoded, method_frame.delivery_tag)
        if request is None:
            # Invalid URL for this queue: ack to remove message, do not create request
            self.server.basic_ack(delivery_tag=method_frame.delivery_tag)
            logger.warning(
                "Discarded message from {} queue (URL did not match): {}",
                self.meta_label,
                encoded[:200],
            )
        else:
            logger.debug(
                "From {} crawl queue: {}",
                self.meta_label,
                self.key,
            )
        return request

    def _decode_request(self, encoded_request, delivery_tag):
        """Decode body; return Request or None if URL does not match this queue (strict URL handling)."""
        url, entry_point = _parse_crawl_message(encoded_request)
        if not url:
            return None
        if self.meta_label == "crunchbase":
            if not _is_crunchbase_url(url):
                return None
        else:  # tracxn
            if not _is_tracxn_url(url):
                return None
        return generateRequest(
            url, delivery_tag, queue=self.meta_label, entry_point=entry_point
        )

    def clear(self):
        if self.key is not None:
            self.server.queue_purge(self.key)


