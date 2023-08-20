from confluent_kafka import Producer
import json
from CrunchyCrawler.rabbitmq.connection import from_settings
from scrapy.exceptions import DropItem


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
        print("Sending to data pipeline",item)
        json_data = json.dumps(dict(item))

        # Send the JSON data to the Kafka topic
        self.producer.produce(self.topic, value=json_data)
        self.producer.flush()
        return item


class RabbitMQPipeline:
    def __init__(self, channel):
        self.channel = channel

    @classmethod
    def from_crawler(cls, crawler):
        channel = from_settings()
        return cls(channel)

    def open_spider(self, spider):
        pass

    def close_spider(self, spider):
        pass

# TODO: refactor this and make it clear
    def process_item(self, item, spider):
        print("item -----> ", item)
        try:
            response = item['_response']
            delivery_tag = item.get('delivery_tag')
            print("RabbitMQ Pipeline", response, item)
            if delivery_tag:
                print({"response": response})
                if response == 200:
                    print("RabbitMQ Sent ack", delivery_tag)
                    self.channel.basic_ack(delivery_tag=delivery_tag)
                else:
                    print("RabbitMQ Sent nack", delivery_tag)
                    self.channel.basic_nack(
                        delivery_tag=delivery_tag, requeue=True)
                    raise DropItem(
                        f"Item dropped due to unsuccessful response. URL: {item.get('crunchbase_url')}, Status Code: {response}")
                del item['_response']
                del item['delivery_tag']
        except Exception as e:
            print("Error from RabbitMQ Pipeline", e)
            raise DropItem(
                f"Crawling failed with exception: {str(e)}, item dropped")
        return item
