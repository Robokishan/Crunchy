

import pika
from django.conf import settings

queue = settings.RB_MAIN_QUEUE
exchange = settings.RB_MAIN_EXCHANGE
routing_key = settings.RB_MAIN_ROUTING_KEY
connection_string = settings.RABBITMQ_URL


class RabbitMQManager:
    _channel = None

    @classmethod
    def set_channel(cls, channel):
        cls._channel = channel

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
    def _publish(cls, message):
        cls._channel.basic_publish(
            exchange=exchange, routing_key=routing_key, body=message, properties=pika.BasicProperties(
                delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE
            ))

    @staticmethod
    def connect_to_rabbitmq():
        parameters = pika.URLParameters(connection_string)
        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()
        channel.add_on_return_callback(RabbitMQManager.handle_basic_return)
        connection.add_on_connection_blocked_callback(
            RabbitMQManager.handle_connection_blocked)
        channel.queue_declare(queue=queue, durable=True)
        channel.exchange_declare(exchange=exchange, exchange_type="direct")
        channel.queue_bind(queue=queue, exchange=exchange,
                           routing_key=routing_key)
        print("Connected to RabbitMQ")
        RabbitMQManager.set_channel(channel)

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
