from CrunchyCrawler.rabbitmq.connection import from_settings
from CrunchyCrawler.agents import AGENTS
import random

'''
PROXY SERVERS TBD
'''

class CrunchyHttpProxyMiddleware(object):
    def process_request(self, request, spider):
        ip = "119.8.10.18:7890"
        request.meta['playwright_context_kwargs'] = {
            "proxy": {
                "server": "https://"+ip,
            }}


class CrunchyUserAgentMiddleware(object):
    def process_request(self, request, spider):
        agent = random.choice(AGENTS)
        request.headers['User-Agent'] = agent

class RabbitMQMiddleware(object):
    def __init__(self, channel):
        self.channel = channel

    @classmethod
    def from_crawler(cls, crawler):
        channel = from_settings()
        return cls(channel)
    
    # only send ack or nack incase of final result
    def process_response(self, request, response, spider):
        print("process_response" , request.meta, response, response.status)
        return response

    def process_exception(self, request, exception, spider):
        delivery_tag = request.meta.get('delivery_tag')
        print(f"process_exception: {delivery_tag}", request.meta, exception)
        self.nack(delivery_tag)
        return None

    def nack(self, delivery_tag):
        print("RQ:DownloadMiddleware:Sending nack for", delivery_tag)
        self.channel.basic_nack(delivery_tag=delivery_tag, requeue=True)

class RabbitMQSpiderMiddleware:
    def __init__(self, channel):
        self.channel = channel

    @classmethod
    def from_crawler(cls, crawler):
        channel = from_settings()
        return cls(channel)
    
    def nack(self, delivery_tag):
        print("RQSpider Middleware:Sending nack for", delivery_tag)
        self.channel.basic_nack(delivery_tag=delivery_tag, requeue=True)

    def process_spider_exception(self, response, exception, spider):
        delivery_tag = response.meta.get('delivery_tag', None)
        print(f"process_spider_exception {delivery_tag}", response.meta, exception, spider)
        if delivery_tag:
            self.nack(delivery_tag)