import pika
from scrapy.utils.project import get_project_settings
from loguru import logger

settings = get_project_settings()

connection_dsn = settings.get('RABBITMQ_URL') + '?heartbeat=0'
queue_name = settings.get(
    'RB_MAIN_QUEUE')
exchange = settings.get('RB_MAIN_EXCHANGE')
routing_key = settings.get('RB_MAIN_ROUTING_KEY')

priority_exchange = settings.get('RABBIT_MQ_PRIORITY_EXCHANGE')
priority_routing_key = settings.get('RABBIT_MQ_PRIORITY_ROUTING_KEY')
priority_queue = settings.get('RABBIT_MQ_PRIORITY_QUEUE')

# Connect to RabbitMQ
parameters = pika.URLParameters(connection_dsn)
connection = pika.BlockingConnection(parameters)
channel = connection.channel(1)
priority_channel = connection.channel(5)

# MAIN QUEUE binding with exchange and routing key
channel.exchange_declare(exchange=exchange, exchange_type='direct')
channel.queue_declare(queue=queue_name, durable=True)
channel.queue_bind(queue=queue_name, exchange=exchange,
                   routing_key=routing_key)

# PRIORITY QUEUE binding with exchange and routing key
priority_channel.exchange_declare(
    exchange=priority_exchange, exchange_type='direct')
priority_channel.queue_declare(queue=priority_queue, durable=True)
priority_channel.queue_bind(queue=priority_queue, exchange=priority_exchange,
                            routing_key=priority_routing_key)

def get_channels():
    logger.debug("Getting RabbitMQ Channel Instance")
    return channel, priority_channel


def close(channel):
    channel.close()
