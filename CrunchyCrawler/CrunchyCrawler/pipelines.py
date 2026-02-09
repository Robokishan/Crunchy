import json
import pika
from CrunchyCrawler.rabbitmq.connection import get_channels
from scrapy.exceptions import DropItem
from loguru import logger


class DatabucketPipeline:
    """
    RabbitMQ pipeline that routes scraped items to databucket queues by source.

    - Items with source='crunchbase' go to crunchbase_databucket_queue
    - Items with source='tracxn' go to tracxn_databucket_queue

    Same behaviour as previous Kafka pipeline, using RabbitMQ only.
    """

    @classmethod
    def from_crawler(cls, crawler):
        settings = crawler.settings
        exchange = settings.get('RB_DATABUCKET_EXCHANGE', 'databucket_exchange')
        crunchbase_rk = settings.get('RB_DATABUCKET_CRUNCHBASE_RK', 'crunchbase_databucket')
        tracxn_rk = settings.get('RB_DATABUCKET_TRACXN_RK', 'tracxn_databucket')
        return cls(
            exchange=exchange,
            crunchbase_routing_key=crunchbase_rk,
            tracxn_routing_key=tracxn_rk,
            rabbitmq_url=settings.get('RABBITMQ_URL'),
        )

    def __init__(self, exchange, crunchbase_routing_key, tracxn_routing_key, rabbitmq_url):
        self.exchange = exchange
        self.crunchbase_routing_key = crunchbase_routing_key
        self.tracxn_routing_key = tracxn_routing_key
        self.rabbitmq_url = rabbitmq_url
        self._connection = None
        self._channel = None

    def open_spider(self, spider):
        if not self.rabbitmq_url:
            logger.warning("RABBITMQ_URL not set; DatabucketPipeline will not publish")
            return
        try:
            parameters = pika.URLParameters(self.rabbitmq_url + '?heartbeat=600')
            self._connection = pika.BlockingConnection(parameters)
            self._channel = self._connection.channel()
            self._channel.exchange_declare(
                exchange=self.exchange,
                exchange_type='direct',
                durable=True,
            )
            logger.info(f"DatabucketPipeline connected to RabbitMQ, exchange={self.exchange}")
        except Exception as e:
            logger.error(f"DatabucketPipeline failed to connect to RabbitMQ: {e}")
            self._channel = None
            self._connection = None

    def close_spider(self, spider):
        if self._channel and self._channel.is_open:
            try:
                self._channel.close()
            except Exception as e:
                logger.debug(f"DatabucketPipeline channel close: {e}")
        if self._connection and self._connection.is_open:
            try:
                self._connection.close()
            except Exception as e:
                logger.debug(f"DatabucketPipeline connection close: {e}")
        self._channel = None
        self._connection = None

    def process_item(self, item, spider):
        if self._channel is None or not self._channel.is_open:
            logger.warning("DatabucketPipeline: no channel, skipping publish")
            return item

        source = item.get('source', 'crunchbase')
        if source == 'tracxn':
            routing_key = self.tracxn_routing_key
        else:
            routing_key = self.crunchbase_routing_key

        # Don't publish internal/retry items
        if source in ('retry', 'unknown'):
            return item

        try:
            json_data = json.dumps(dict(item))
            self._channel.basic_publish(
                exchange=self.exchange,
                routing_key=routing_key,
                body=json_data,
                properties=pika.BasicProperties(
                    delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE,
                    content_type='application/json',
                ),
            )
            logger.info(f"Sent to databucket ({source} -> {routing_key}): {item.get('name', item.get('url', '?'))}")
        except Exception as e:
            logger.error(f"DatabucketPipeline publish failed: {e}")
        return item


class RabbitMQPipeline:
    def __init__(self, cb_channel, tracxn_channel):
        self.channels = {
            'crunchbase': cb_channel,
            'tracxn': tracxn_channel,
        }

    @classmethod
    def from_crawler(cls, crawler):
        cb_channel, tracxn_channel = get_channels()
        return cls(cb_channel, tracxn_channel)

    def open_spider(self, spider):
        pass

    def close_spider(self, spider):
        pass

# TODO: refactor this and make it clear
    def process_item(self, item, spider):
        logger.debug(f"item -----> {item}")
        try:
            response = item['_response']
            delivery_tag = item.get('delivery_tag')
            queue = item.get('queue')
            channel = self.channels.get(queue)
            logger.debug(f"RabbitMQ Pipeline: {response} {item}")
            if delivery_tag:
                logger.debug(f"response: {response}")
                if response == 200:
                    if channel is not None:
                        logger.info(f"RabbitMQ Sent ack: {delivery_tag}")
                        channel.basic_ack(delivery_tag=delivery_tag)
                else:
                    if channel is not None:
                        logger.info(f"RabbitMQ Sent nack: {delivery_tag}")
                        channel.basic_nack(
                            delivery_tag=delivery_tag, requeue=True)
                    raise DropItem(
                        f"Item dropped due to unsuccessful response. URL: {item.get('crunchbase_url')}, Status Code: {response}")
                del item['_response']
                del item['delivery_tag']
                del item['queue']
        except Exception as e:
            logger.error(f"Error from RabbitMQ Pipeline: {e}")
            raise DropItem(
                f"Crawling failed with exception: {str(e)}, item dropped")
        return item
