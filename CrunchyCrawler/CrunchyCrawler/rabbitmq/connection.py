import pika
from scrapy.utils.project import get_project_settings


settings = get_project_settings()

queue_name = settings.get(
    'RB_MAIN_QUEUE')
connection_dsn = settings.get('RABBITMQ_URL') + '?heartbeat=0'
exchange = settings.get('RB_MAIN_EXCHANGE')
routing_key = settings.get('RB_MAIN_ROUTING_KEY')

# Connect to RabbitMQ
parameters = pika.URLParameters(connection_dsn)
connection = pika.BlockingConnection(parameters)
channel = connection.channel()

# MAIN QUEUE binding with exchange and routing key
channel.exchange_declare(exchange=exchange, exchange_type='direct')
channel.queue_declare(queue=queue_name, durable=True)
channel.queue_bind(queue=queue_name, exchange=exchange,
                   routing_key=routing_key)


def from_settings():
    print("Getting RabbitMQ Channel Instance")
    return channel


def close(channel):
    channel.close()
