import pika
from scrapy.utils.project import get_project_settings
from loguru import logger

settings = get_project_settings()

connection_dsn = settings.get('RABBITMQ_URL') + '?heartbeat=0'

# Crawl queues (decoupled: Crunchbase and Tracxn)
crawl_exchange = settings.get('RB_CRAWL_EXCHANGE', 'crawl_exchange')
cb_queue = settings.get('RB_CRUNCHBASE_CRAWL_QUEUE', 'crawl_crunchbase_queue')
cb_rk = settings.get('RB_CRUNCHBASE_CRAWL_RK', 'crawl_crunchbase')
tracxn_queue = settings.get('RB_TRACXN_CRAWL_QUEUE', 'crawl_tracxn_queue')
tracxn_rk = settings.get('RB_TRACXN_CRAWL_RK', 'crawl_tracxn')

# Connect to RabbitMQ
parameters = pika.URLParameters(connection_dsn)
connection = pika.BlockingConnection(parameters)

internal_channel = connection.channel(1)
cb_channel = connection.channel(2)
tracxn_channel = connection.channel(5)

# Crawl exchange and Crunchbase queue
cb_channel.exchange_declare(exchange=crawl_exchange, exchange_type='direct')
cb_channel.queue_declare(queue=cb_queue, durable=True)
cb_channel.queue_bind(queue=cb_queue, exchange=crawl_exchange, routing_key=cb_rk)

# Tracxn queue (same exchange)
tracxn_channel.exchange_declare(exchange=crawl_exchange, exchange_type='direct')
tracxn_channel.queue_declare(queue=tracxn_queue, durable=True)
tracxn_channel.queue_bind(queue=tracxn_queue, exchange=crawl_exchange, routing_key=tracxn_rk)


def get_channels():
    """Return (cb_channel, tracxn_channel) for scheduler/pipeline (main/priority)."""
    logger.debug("Getting RabbitMQ Channel Instance")
    return cb_channel, tracxn_channel


def get_internal_channel():
    return internal_channel


def close(channel):
    channel.close()
