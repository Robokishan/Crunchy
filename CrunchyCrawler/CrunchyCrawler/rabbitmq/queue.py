from scrapy.utils.request import request_from_dict
import pickle
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


class MainQueue():

    def __init__(self, server, spider, key=None, exchange=None):
        """Initialize per-spider RabbitMQ queue.
        Parameters:
            server -- rabbitmq connection
            spider -- spider instance
            key -- key for this queue (e.g. "%(spider)s:queue")
        """
        self.server = server
        self.spider = spider

        # key is just queue name
        self.key = key
        logger.debug(f"Main queue: {self.key}")

    def __len__(self):
        response = self.server.queue_declare(
            self.key, passive=True)
        return response.method.message_count

    def push(self, request):
        pass

    def pop(self):
        method_frame, header, body = self.server.basic_get(queue=self.key)
        logger.debug(f"Response from main queue ", body, method_frame, header, self.key)
        if body != None:
            return self._decode_request(body.decode('utf-8'), method_frame.delivery_tag)

    # i don't think this will require
    def _encode_request(self, request):
        """Encode a request object"""
        return pickle.dumps(request.to_dict(spider=self.spider))

    def _decode_request(self, encoded_request, delivery_tag):
        """Decode an request previously encoded"""
        return generateRequest(encoded_request, delivery_tag, queue="normal")

    def clear(self):
        """Clear queue/stack"""
        self.server.queue_purge(self.key)

class PriorityQueue():

    def __init__(self, server, spider, key=None, exchange=None):
        """Initialize per-spider RabbitMQ queue.
        Parameters:
            server -- rabbitmq connection
            spider -- spider instance
            key -- key for this queue (e.g. "%(spider)s:queue")
        """
        self.server = server
        self.spider = spider

        # key is just queue name
        self.key = key
        logger.info(f"Priority queue: {self.key}")

    def __len__(self):
        response = self.server.queue_declare(
            self.key, passive=True)
        return response.method.message_count

    def push(self, request):
        pass

    def pop(self):
        method_frame, header, body = self.server.basic_get(queue=self.key)
        logger.info(f"Response from priority queue: {body} ,{method_frame}, {header}, {self.key}")
        if body != None:
            return self._decode_request(body.decode('utf-8'), method_frame.delivery_tag)

    # i don't think this will require
    def _encode_request(self, request):
        """Encode a request object"""
        return pickle.dumps(request.to_dict(spider=self.spider))

    def _decode_request(self, encoded_request, delivery_tag):
        """Decode an request previously encoded"""
        return generateRequest(encoded_request, delivery_tag, queue="priority")

    def clear(self):
        """Clear queue/stack"""
        self.server.queue_purge(self.key)


    

