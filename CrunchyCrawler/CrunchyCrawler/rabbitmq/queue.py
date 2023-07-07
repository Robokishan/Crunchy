from scrapy.utils.reqser import request_to_dict, request_from_dict
import pickle
from scrapy import Request
from scrapy_playwright.page import PageMethod
from scrapy.spidermiddlewares.httperror import HttpError


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
        print("starting here -->", key % {'spider': spider.name})
        self._declare_queue()

    def _declare_queue(self):
        pass

    def _encode_request(self, request):
        """Encode a request object"""
        return pickle.dumps(request_to_dict(request, self.spider))

    def _decode_request(self, encoded_request):
        """Decode an request previously encoded"""
        return request_from_dict(pickle.loads(encoded_request), self.spider)

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
        print("Declaring queue", self.key)
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
            self.server.basic_ack(delivery_tag=method_frame.delivery_tag)
            return self._decode_request(body)


class MainQueue():

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9',  # this is game changing header
    }

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
        print("Main queue", self.key)

    def __len__(self):
        response = self.server.queue_declare(
            self.key, passive=True)
        return response.method.message_count

    def push(self, request):
        pass

    def pop(self):
        method_frame, header, body = self.server.basic_get(queue=self.key)
        print("Response from main queue", body, method_frame, header, self.key)
        if body != None:
            return self._decode_request(body.decode('utf-8'), method_frame.delivery_tag)

    # i don't think this will require
    def _encode_request(self, request):
        """Encode a request object"""
        return pickle.dumps(request_to_dict(request, self.spider))

    def _decode_request(self, encoded_request, delivery_tag):
        """Decode an request previously encoded"""
        return self.request(encoded_request, delivery_tag)

    def clear(self):
        """Clear queue/stack"""
        self.server.queue_purge(self.key)

    def request(self, url, delivery_tag):
        return Request(url,
                       headers=self.headers,
                       errback=self.errback,
                       meta={
                           "delivery_tag": delivery_tag,
                           # this is just a default ip address It will be changed in middleware
                           #   "playwright_context_kwargs": {
                           #       "proxy": {
                           #           "server": "http://147.135.54.182:3128",
                           #       },
                           #   },
                           "playwright": True,
                           #    "playwright_include_page": True,
                           "playwright_page_methods": [
                               PageMethod(
                                   "wait_for_load_state", "networkidle")
                           ],
                       })

    async def errback(self, failure):
        if failure.check(HttpError):
            # you can get the response
            response = failure.value.response
            request = failure.request
            print('HttpError on ', request)

            # try:
            #     page = response.meta["playwright_page"]
            #     await page.close()
            # except Exception as e:
            #     print("Closing Playwright from queue", e)

            # check response
            try:
                print("HttpError on", response.url)
                delivery_tag = response.meta.get('delivery_tag')
                print("Delivery tag", delivery_tag)
                if response.status == 404:
                    return self.server.basic_ack(delivery_tag=delivery_tag)

            except Exception as e:
                print("Http error something went wrong", e)
            self.server.basic_nack(
                delivery_tag=delivery_tag, requeue=True)
        else:
            print("Other error from scrapy", failure)
            try:
                request = failure.request
                delivery_tag = request.meta.get('delivery_tag')
                print("Other services", delivery_tag)
                self.server.basic_nack(delivery_tag=delivery_tag, requeue=True)
            except Exception as e:
                print("Rabbitmq other error something went wrong", e)
