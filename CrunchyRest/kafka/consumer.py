from confluent_kafka import Consumer, Producer as KafkaProducer
import json
from django.conf import settings


class Subscriber:
    """Kafka subscriber for Crunchbase topic (default)."""
    service = None
    broker_url = None
    topic_names = None
    group_id = None
    handler = None
    consumer = None

    def __init__(self, callback, topic=None):
        self.callback = callback
        # Allow custom topic, default to crunchbase topic
        self.topic = topic or settings.KAFKA_CRUNCHBASE_DATABUCKET_TOPIC

    def connect(self):
        # Consumer configuration
        consumer_conf = {
            'bootstrap.servers': settings.KAFKA_SERVER,
            'group.id': settings.KAFKA_GROUP_ID,
            'auto.offset.reset': 'latest',
            'sasl.mechanism': settings.KAFKA_SASL_MECHANISM,
            'ssl.ca.location': settings.KAFKA_CA_CERTIFICATE_PATH,
            'security.protocol': 'SASL_SSL',
            'sasl.username': settings.KAFKA_USERNAME,
            'sasl.password': settings.KAFKA_PASSWORD
        }

        print("Consumer Connecting to Kafka...")
        # Create a Kafka consumer
        self.consumer = Consumer(consumer_conf)
        print("Consumer Connected")
        self.consumer.subscribe([self.topic])
        print(f"Subscribed to topic: {self.topic}")

    def run(self):
        while True:
            # msg = self.consumer.poll(1.0)
            msgs = self.consumer.consume(num_messages=1, timeout=1.0)
            for msg in msgs:
                print(msg)
                if msg is None:
                    continue
                if msg.error():
                    print("Error: {}".format(msg.error()))
                    continue
                data = msg.value()
                try:
                    data = json.loads(data)
                    print("Received", data)
                    if self.callback(data) == True:
                        self.consumer.commit(message=msg, asynchronous=False)
                except Exception as e:
                    print(e)


class TracxnSubscriber(Subscriber):
    """Kafka subscriber specifically for Tracxn topic."""
    
    def __init__(self, callback):
        super().__init__(callback, topic=settings.KAFKA_TRACXN_DATABUCKET_TOPIC)


class Producer:
    def connect(self):
        producer_conf = {
            'bootstrap.servers': settings.KAFKA_SERVER,
            'sasl.mechanism': settings.KAFKA_SASL_MECHANISM,
            'security.protocol': 'SASL_SSL',
            'sasl.username': settings.KAFKA_USERNAME,
            'sasl.password': settings.KAFKA_PASSWORD
        }
        print("Producer Connecting to Kafka...")
        self.producer = KafkaProducer(producer_conf)
        print("Producer Connected")
    
    def publish(self, data):
        self.producer.produce(settings.KAFKA_CRUNCHBASE_DATABUCKET_TOPIC, data.encode('utf-8'))
        self.producer.flush()
        


