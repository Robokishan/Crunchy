from CrunchyCrawler.rabbitmq.connection import get_channels
from CrunchyCrawler.agents import AGENTS
import random
from loguru import logger

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
        logger.info(f"Selected agent: {agent}")
        
    def process_exception(self, request, exception, spider):
        logger.error(f"Error in CrunchyUserAgentMiddleware {exception}")
        return None

class RabbitMQMiddleware(object):
    def __init__(self, channel, priority_channel):
        self.channel = channel
        self.priority_channel = priority_channel
        self.channels = {
            'normal': channel,
            'priority': priority_channel,
        }


    @classmethod
    def from_crawler(cls, crawler):
        channel, priority_channel = get_channels()
        return cls(channel, priority_channel)
    
    # only send ack or nack incase of final result
    def process_response(self, request, response, spider):
        logger.debug("process_response" , request.meta, response, response.status)
        return response

    def process_exception(self, request, exception, spider):
        delivery_tag = request.meta.get('delivery_tag')
        queue = request.meta.get('queue')
        logger.error(f"process_exception: {delivery_tag}", request.meta, exception)
        if delivery_tag:
            self.nack(delivery_tag, queue)
        return None

    def nack(self, delivery_tag, queue):
        logger.warning("RQ:DownloadMiddleware:Sending nack for", delivery_tag)
        channel = self.channels.get(queue)
        if channel is not None:
            channel.basic_nack(delivery_tag=delivery_tag, requeue=True)

class RabbitMQSpiderMiddleware:
    def __init__(self, channel, priority_channel):
        self.channel = channel
        self.priority_channel = priority_channel
        self.channels = {
            'normal': channel,
            'priority': priority_channel,
        }

    @classmethod
    def from_crawler(cls, crawler):
        channel, priority_channel = get_channels()
        return cls(channel, priority_channel)
    
    def nack(self, delivery_tag, queue):
        channel = self.channels.get(queue)
        logger.warning(f"RQSpider Middleware checking Channel: {channel} for delivery:{delivery_tag}")
        if channel is not None:
            logger.warning(f"RQSpider Middleware:Sending nack for: {delivery_tag}")
            channel.basic_nack(delivery_tag=delivery_tag, requeue=True)

    def process_spider_exception(self, response, exception, spider):
        delivery_tag = response.meta.get('delivery_tag', None)
        queue = response.meta.get('queue')
        logger.error(f"process_spider_exception: {exception} delivery:{delivery_tag} queue:{queue} {response.meta} ")
        logger.exception(exception)
        if delivery_tag:
            self.nack(delivery_tag, queue)
        return None



# dummy test middleware
class TestSpiderMiddleware1:
    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        return s
    
    def process_spider_exception(self, response, exception, spider):
        logger.error(f"process_spider_exception1 {response.meta} {exception} {spider}")
        return None