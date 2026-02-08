

import pika
import json
from django.conf import settings

queue = settings.RB_MAIN_QUEUE
exchange = settings.RB_MAIN_EXCHANGE
routing_key = settings.RB_MAIN_ROUTING_KEY

priority_queue = settings.RABBIT_MQ_PRIORITY_QUEUE
priority_exchange = settings.RABBIT_MQ_PRIORITY_EXCHANGE
priority_routing_key = settings.RABBIT_MQ_PRIORITY_ROUTING_KEY

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

    @classmethod
    def set_channel(cls, channel):
        cls._channel = channel

    @classmethod
    def set_priority_channel(cls, channel):
        cls._priority_channel = channel

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
    def publish_message(cls, message):

        try:

            if cls._channel is None:
                raise Exception(
                    "RabbitMQ channel is not set. Make sure to connect to RabbitMQ first.")

            # Your code to publish the message using the channel
            RabbitMQManager._publish(message)
        except Exception as e:
            RabbitMQManager.connect_to_rabbitmq()
            RabbitMQManager._publish(message)

    @classmethod
    def publish_priority_message(cls, message):
        try:

            if cls._priority_channel is None:
                raise Exception(
                    "RabbitMQ channel is not set. Make sure to connect to RabbitMQ first.")

            # Your code to publish the message using the channel
            RabbitMQManager._priority_publish(message)
        except Exception as e:
            RabbitMQManager.connect_to_rabbitmq()
            RabbitMQManager._priority_publish(message)

    @classmethod
    def _publish(cls, message):
        cls._channel.basic_publish(
            exchange=exchange, routing_key=routing_key, body=message, properties=pika.BasicProperties(
                delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE
            ))

    @classmethod
    def _priority_publish(cls, message):
        cls._priority_channel.basic_publish(
            exchange=priority_exchange, routing_key=priority_routing_key, body=message, properties=pika.BasicProperties(
                delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE
            ))

    @staticmethod
    def connect_to_rabbitmq():
        if settings.RABBITMQ_URL is None:
            return
        parameters = pika.URLParameters(connection_string)
        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()
        priority_channel = connection.channel()
        databucket_channel = connection.channel()
        channel.add_on_return_callback(RabbitMQManager.handle_basic_return)
        connection.add_on_connection_blocked_callback(
            RabbitMQManager.handle_connection_blocked)
        channel.queue_declare(queue=queue, durable=True)
        channel.exchange_declare(exchange=exchange, exchange_type="direct")
        channel.queue_bind(queue=queue, exchange=exchange,
                           routing_key=routing_key)

        priority_channel.queue_declare(queue=priority_queue, durable=True)
        priority_channel.exchange_declare(
            exchange=priority_exchange, exchange_type="direct")
        priority_channel.queue_bind(queue=priority_queue, exchange=priority_exchange,
                                    routing_key=priority_routing_key)

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
        RabbitMQManager.set_channel(channel)
        RabbitMQManager.set_priority_channel(priority_channel)
        RabbitMQManager.set_databucket_channel(databucket_channel)

    @staticmethod
    def get_pending_in_priority_queue():
        if settings.RABBITMQ_URL is None:
            return None

        if RabbitMQManager._priority_channel is None or RabbitMQManager._priority_channel.is_closed:
            try:
                RabbitMQManager.connect_to_rabbitmq()
            except Exception as e:
                pass
            return None

        queue_state = RabbitMQManager._priority_channel.queue_declare(
            queue=priority_queue, passive=True
        )
        return queue_state.method.message_count

    @staticmethod
    def get_pending_in_normal_queue():
        if settings.RABBITMQ_URL is None:
            return None

        if RabbitMQManager._channel is None or RabbitMQManager._priority_channel.is_closed:
            try:
                RabbitMQManager.connect_to_rabbitmq()
            except Exception as e:
                pass
            return None

        queue_state = RabbitMQManager._channel.queue_declare(
            queue=queue, passive=True
        )
        return queue_state.method.message_count

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
