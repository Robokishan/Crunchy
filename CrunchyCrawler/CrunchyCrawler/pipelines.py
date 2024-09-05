from confluent_kafka import Producer
import json
from CrunchyCrawler.rabbitmq.connection import get_channels
from scrapy.exceptions import DropItem
from loguru import logger


class KafkaPipeline:

    @classmethod
    def from_crawler(cls, crawler):
        settings = crawler.settings

        producer_conf = {
            'bootstrap.servers': settings.get('KAFKA_SERVER'),
            'sasl.mechanism': settings.get('KAFKA_SASL_MECHANISM'),
            'security.protocol': 'SASL_SSL',
            'sasl.username': settings.get('KAFKA_USERNAME'),
            'sasl.password': settings.get('KAFKA_PASSWORD')
        }

        topic = settings.get('KAFKA_CRUNCHBASE_DATABUCKET_TOPIC')

        # Initialize the pipeline with the desired setting
        return cls(producer_conf, topic)

    def __init__(self, producer_conf, topic):
        # Create a Kafka producer
        self.producer = Producer(producer_conf)
        self.topic = topic

    def process_item(self, item, spider):
        # Serialize the item as JSON
        logger.info(f"Sent to Bucket: {item}")
        json_data = json.dumps(dict(item))

        # Send the JSON data to the Kafka topic
        self.producer.produce(self.topic, value=json_data)
        self.producer.flush()
        return item


class RabbitMQPipeline:
    def __init__(self, channel, priority_channel):
        self.channel = channel
        self.priority_channel = priority_channel
        self.channels = {
            'normal': self.channel,
            'priority': self.priority_channel,
        }

    @classmethod
    def from_crawler(cls, crawler):
        channel, priority_channel = get_channels()
        return cls(channel, priority_channel)

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
                    logger.info(f"RabbitMQ Sent ack: {delivery_tag}")
                    channel.basic_ack(delivery_tag=delivery_tag)
                else:
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
