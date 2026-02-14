import json
import pika
from CrunchyCrawler.rabbitmq.connection import get_channels, get_databucket_channel
from scrapy.exceptions import DropItem
from loguru import logger

# Keys that must not be sent to databucket (crawl-internal only)
DATABUCKET_SKIP_KEYS = frozenset(('_response', 'delivery_tag', 'queue'))


def _serialize_item_for_databucket(item):
    """Build a JSON-serializable dict for databucket, excluding internal keys."""
    payload = {k: v for k, v in item.items() if k not in DATABUCKET_SKIP_KEYS}
    return json.dumps(payload, default=str)


class DatabucketPipeline:
    """
    RabbitMQ pipeline that routes scraped items to databucket queues by source.

    - Items with source='crunchbase' go to crunchbase_databucket_queue
    - Items with source='tracxn' go to tracxn_databucket_queue

    Uses the same RabbitMQ connection as the crawl pipeline so publish works whenever ack works.
    """

    @classmethod
    def from_crawler(cls, crawler):
        settings = crawler.settings
        exchange = settings.get('RB_DATABUCKET_EXCHANGE', 'databucket_exchange')
        crunchbase_rk = settings.get('RB_DATABUCKET_CRUNCHBASE_RK', 'crunchbase_databucket')
        tracxn_rk = settings.get('RB_DATABUCKET_TRACXN_RK', 'tracxn_databucket')
        channel = get_databucket_channel()
        rabbitmq_url = settings.get('RABBITMQ_URL')
        return cls(
            exchange=exchange,
            crunchbase_routing_key=crunchbase_rk,
            tracxn_routing_key=tracxn_rk,
            channel=channel,
            rabbitmq_url=rabbitmq_url,
        )

    def __init__(self, exchange, crunchbase_routing_key, tracxn_routing_key, channel, rabbitmq_url=None):
        self.exchange = exchange
        self.crunchbase_routing_key = crunchbase_routing_key
        self.tracxn_routing_key = tracxn_routing_key
        self._channel = channel
        self._rabbitmq_url = rabbitmq_url
        self._fallback_connection = None
        self._fallback_channel = None

    def _ensure_channel(self):
        """Use shared channel if open; else open a dedicated connection and use its channel."""
        if self._channel is not None and self._channel.is_open:
            return self._channel
        if self._fallback_channel is not None and self._fallback_channel.is_open:
            return self._fallback_channel
        if not self._rabbitmq_url:
            return None
        try:
            if self._fallback_connection is not None:
                try:
                    self._fallback_connection.close()
                except Exception:
                    pass
                self._fallback_connection = None
                self._fallback_channel = None
            parameters = pika.URLParameters(self._rabbitmq_url + '?heartbeat=600')
            self._fallback_connection = pika.BlockingConnection(parameters)
            self._fallback_channel = self._fallback_connection.channel()
            self._fallback_channel.exchange_declare(
                exchange=self.exchange,
                exchange_type='direct',
                durable=True,
            )
            logger.info("DatabucketPipeline: using fallback RabbitMQ connection for publish")
            return self._fallback_channel
        except Exception as e:
            logger.error(f"DatabucketPipeline: fallback connection failed: {e}")
            return None

    def open_spider(self, spider):
        if self._channel and self._channel.is_open:
            logger.info(f"DatabucketPipeline using shared RabbitMQ channel, exchange={self.exchange}")
        else:
            logger.warning("DatabucketPipeline: shared channel not open; will use fallback connection when publishing")

    def close_spider(self, spider):
        if self._fallback_channel and self._fallback_channel.is_open:
            try:
                self._fallback_channel.close()
            except Exception as e:
                logger.debug(f"DatabucketPipeline fallback channel close: {e}")
        if self._fallback_connection and self._fallback_connection.is_open:
            try:
                self._fallback_connection.close()
            except Exception as e:
                logger.debug(f"DatabucketPipeline fallback connection close: {e}")
        self._fallback_channel = None
        self._fallback_connection = None

    def process_item(self, item, spider):
        source = item.get('source', 'crunchbase')
        channel = self._ensure_channel()
        channel_ok = channel is not None
        logger.debug(
            "DatabucketPipeline process_item: source=%s channel_ok=%s name=%s",
            source, channel_ok, item.get('name') or item.get('url'),
        )
        if not channel_ok:
            logger.warning("DatabucketPipeline: no channel, skipping publish")
            return item

        if source == 'tracxn':
            routing_key = self.tracxn_routing_key
        else:
            routing_key = self.crunchbase_routing_key

        # Don't publish internal/retry items
        if source in ('retry', 'unknown'):
            return item

        try:
            json_data = _serialize_item_for_databucket(item)
        except Exception as e:
            logger.error(f"DatabucketPipeline serialization failed: {e}")
            return item

        for attempt in (1, 2):
            try:
                channel = self._ensure_channel()
                if channel is None:
                    return item
                channel.basic_publish(
                    exchange=self.exchange,
                    routing_key=routing_key,
                    body=json_data,
                    properties=pika.BasicProperties(
                        delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE,
                        content_type='application/json',
                    ),
                )
                logger.info(f"Sent to databucket ({source} -> {routing_key}): {item.get('name', item.get('url', '?'))}")
                return item
            except Exception as e:
                logger.warning(f"DatabucketPipeline publish failed (attempt {attempt}/2): {e}")
                if attempt == 1:
                    self._fallback_channel = None
                    self._fallback_connection = None
                if attempt == 2:
                    return item
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

            # Use "is not None" so delivery_tag=0 is still valid
            if delivery_tag is not None:
                logger.debug(f"response: {response}")
                # Normalize: response can be int 200 or string "200"
                ok = (response == 200) or (response == "200")
                if ok:
                    if channel is not None:
                        logger.info(f"RabbitMQ Sent ack: {delivery_tag}")
                        channel.basic_ack(delivery_tag=delivery_tag)
                    del item['_response']
                    del item['delivery_tag']
                    del item['queue']
                else:
                    if channel is not None:
                        logger.info(f"RabbitMQ Sent nack: {delivery_tag}")
                        channel.basic_nack(
                            delivery_tag=delivery_tag, requeue=True)
                    raise DropItem(
                        f"Item dropped due to unsuccessful response. URL: {item.get('crunchbase_url')}, Status Code: {response}")
        except Exception as e:
            logger.error(f"Error from RabbitMQ Pipeline: {e}")
            raise DropItem(
                f"Crawling failed with exception: {str(e)}, item dropped")
        return item
