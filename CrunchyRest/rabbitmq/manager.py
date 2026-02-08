

import pika
import json
from django.conf import settings

# Crawl queues (decoupled: Crunchbase and Tracxn)
crawl_exchange = getattr(settings, 'RB_CRAWL_EXCHANGE', 'crawl_exchange')
crawl_crunchbase_queue = getattr(settings, 'RB_CRUNCHBASE_CRAWL_QUEUE', 'crawl_crunchbase_queue')
crawl_crunchbase_rk = getattr(settings, 'RB_CRUNCHBASE_CRAWL_RK', 'crawl_crunchbase')
crawl_tracxn_queue = getattr(settings, 'RB_TRACXN_CRAWL_QUEUE', 'crawl_tracxn_queue')
crawl_tracxn_rk = getattr(settings, 'RB_TRACXN_CRAWL_RK', 'crawl_tracxn')

# Databucket: queues for scraped items (replaces Kafka topics)
databucket_exchange = getattr(
    settings, 'RB_DATABUCKET_EXCHANGE', 'databucket_exchange'
)
databucket_crunchbase_queue = getattr(
    settings, 'RB_DATABUCKET_CRUNCHBASE_QUEUE', 'crunchbase_databucket_queue'
)
databucket_crunchbase_rk = getattr(
    settings, 'RB_DATABUCKET_CRUNCHBASE_RK', 'crunchbase_databucket'
)
databucket_tracxn_queue = getattr(
    settings, 'RB_DATABUCKET_TRACXN_QUEUE', 'tracxn_databucket_queue'
)
databucket_tracxn_rk = getattr(
    settings, 'RB_DATABUCKET_TRACXN_RK', 'tracxn_databucket'
)

connection_string = settings.RABBITMQ_URL


class RabbitMQManager:
    _channel = None
    _priority_channel = None
    _databucket_channel = None
    _crawl_channel = None

    @classmethod
    def set_channel(cls, channel):
        cls._channel = channel

    @classmethod
    def set_priority_channel(cls, channel):
        cls._priority_channel = channel

    @classmethod
    def set_crawl_channel(cls, channel):
        cls._crawl_channel = channel

    @classmethod
    def set_databucket_channel(cls, channel):
        cls._databucket_channel = channel

    @classmethod
    def publish_crunchbase_item(cls, body):
        """Publish a scraped Crunchbase item (JSON string or dict) to databucket queue."""
        if isinstance(body, dict):
            body = json.dumps(body)
        cls._ensure_databucket_channel()
        if cls._databucket_channel is None:
            return
        cls._databucket_channel.basic_publish(
            exchange=databucket_exchange,
            routing_key=databucket_crunchbase_rk,
            body=body,
            properties=pika.BasicProperties(
                delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE,
                content_type='application/json',
            ),
        )

    @classmethod
    def publish_tracxn_item(cls, body):
        """Publish a scraped Tracxn item (JSON string or dict) to databucket queue."""
        if isinstance(body, dict):
            body = json.dumps(body)
        cls._ensure_databucket_channel()
        if cls._databucket_channel is None:
            return
        cls._databucket_channel.basic_publish(
            exchange=databucket_exchange,
            routing_key=databucket_tracxn_rk,
            body=body,
            properties=pika.BasicProperties(
                delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE,
                content_type='application/json',
            ),
        )

    @classmethod
    def _ensure_databucket_channel(cls):
        if cls._databucket_channel is not None and cls._databucket_channel.is_open:
            return
        try:
            RabbitMQManager.connect_to_rabbitmq()
        except Exception:
            pass

    @classmethod
    def _ensure_crawl_channel(cls):
        if cls._crawl_channel is not None and cls._crawl_channel.is_open:
            return
        try:
            RabbitMQManager.connect_to_rabbitmq()
        except Exception:
            pass

    @classmethod
    def publish_crunchbase_crawl(cls, message):
        """Publish a crawl request to the Crunchbase crawl queue (decoupled)."""
        cls._ensure_crawl_channel()
        if cls._crawl_channel is None:
            return
        body = json.dumps(message) if isinstance(message, dict) else message
        cls._crawl_channel.basic_publish(
            exchange=crawl_exchange,
            routing_key=crawl_crunchbase_rk,
            body=body,
            properties=pika.BasicProperties(
                delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE,
                content_type='application/json',
            ),
        )

    @classmethod
    def publish_tracxn_crawl(cls, message):
        """Publish a crawl request to the Tracxn crawl queue (decoupled)."""
        cls._ensure_crawl_channel()
        if cls._crawl_channel is None:
            return
        body = json.dumps(message) if isinstance(message, dict) else message
        cls._crawl_channel.basic_publish(
            exchange=crawl_exchange,
            routing_key=crawl_tracxn_rk,
            body=body,
            properties=pika.BasicProperties(
                delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE,
                content_type='application/json',
            ),
        )

    @staticmethod
    def connect_to_rabbitmq():
        if settings.RABBITMQ_URL is None:
            return
        parameters = pika.URLParameters(connection_string)
        connection = pika.BlockingConnection(parameters)
        crawl_channel = connection.channel()
        databucket_channel = connection.channel()
        connection.add_on_connection_blocked_callback(
            RabbitMQManager.handle_connection_blocked)

        # Crawl exchange and queues (decoupled Crunchbase / Tracxn)
        crawl_channel.exchange_declare(exchange=crawl_exchange, exchange_type='direct')
        crawl_channel.queue_declare(queue=crawl_crunchbase_queue, durable=True)
        crawl_channel.queue_bind(queue=crawl_crunchbase_queue, exchange=crawl_exchange, routing_key=crawl_crunchbase_rk)
        crawl_channel.queue_declare(queue=crawl_tracxn_queue, durable=True)
        crawl_channel.queue_bind(queue=crawl_tracxn_queue, exchange=crawl_exchange, routing_key=crawl_tracxn_rk)

        # Databucket exchange and queues (for scraped items, replaces Kafka)
        databucket_channel.exchange_declare(
            exchange=databucket_exchange, exchange_type='direct', durable=True
        )
        databucket_channel.queue_declare(queue=databucket_crunchbase_queue, durable=True)
        databucket_channel.queue_bind(
            queue=databucket_crunchbase_queue,
            exchange=databucket_exchange,
            routing_key=databucket_crunchbase_rk,
        )
        databucket_channel.queue_declare(queue=databucket_tracxn_queue, durable=True)
        databucket_channel.queue_bind(
            queue=databucket_tracxn_queue,
            exchange=databucket_exchange,
            routing_key=databucket_tracxn_rk,
        )

        print("Connected to RabbitMQ")
        RabbitMQManager.set_crawl_channel(crawl_channel)
        RabbitMQManager.set_databucket_channel(databucket_channel)

    @staticmethod
    def get_pending_in_priority_queue():
        """Pending messages in Tracxn crawl queue."""
        if settings.RABBITMQ_URL is None:
            return None
        RabbitMQManager._ensure_crawl_channel()
        if RabbitMQManager._crawl_channel is None or not RabbitMQManager._crawl_channel.is_open:
            return None
        try:
            queue_state = RabbitMQManager._crawl_channel.queue_declare(queue=crawl_tracxn_queue, passive=True)
            return queue_state.method.message_count
        except Exception:
            return None

    @staticmethod
    def get_pending_in_normal_queue():
        """Pending messages in Crunchbase crawl queue."""
        if settings.RABBITMQ_URL is None:
            return None
        RabbitMQManager._ensure_crawl_channel()
        if RabbitMQManager._crawl_channel is None or not RabbitMQManager._crawl_channel.is_open:
            return None
        try:
            queue_state = RabbitMQManager._crawl_channel.queue_declare(queue=crawl_crunchbase_queue, passive=True)
            return queue_state.method.message_count
        except Exception:
            return None

    @staticmethod
    def handle_connection_error(connection, error):
        print("Connection Error:", error)

    @staticmethod
    def handle_channel_error(channel, error):
        print("Channel Error:", error)

    @staticmethod
    def handle_basic_return(channel, method, properties, body):
        print("Basic Return - Message Returned:", body)

    @staticmethod
    def handle_connection_blocked(connection, reason):
        print("Connection Blocked:", reason)
