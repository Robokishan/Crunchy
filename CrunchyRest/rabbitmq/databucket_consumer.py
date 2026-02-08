"""
RabbitMQ consumer for databucket queues (replaces Kafka consumers).

Consumes from crunchbase_databucket_queue or tracxn_databucket_queue,
parses JSON body and calls the provided callback. Acks on success, nacks with
requeue on failure.
"""

import json
import pika
from django.conf import settings


def run_consumer(queue_name, routing_key, exchange, callback):
    """
    Consume messages from a databucket queue and invoke callback for each.

    Args:
        queue_name: RabbitMQ queue name (e.g. crunchbase_databucket_queue)
        routing_key: Routing key the queue is bound with
        exchange: Exchange name (databucket_exchange)
        callback: Callable that receives one dict (parsed JSON body). Return True to ack, False to nack+requeue.

    Does not return; runs until interrupted.
    """
    if not settings.RABBITMQ_URL:
        print("RABBITMQ_URL not set. Exiting.")
        return

    parameters = pika.URLParameters(settings.RABBITMQ_URL + '?heartbeat=600')
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()

    channel.exchange_declare(exchange=exchange, exchange_type='direct', durable=True)
    channel.queue_declare(queue=queue_name, durable=True)
    channel.queue_bind(
        queue=queue_name,
        exchange=exchange,
        routing_key=routing_key,
    )
    channel.basic_qos(prefetch_count=1)

    def on_message(ch, method, properties, body):
        try:
            data = json.loads(body)
            if callback(data) is True:
                ch.basic_ack(delivery_tag=method.delivery_tag)
            else:
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
        except Exception as e:
            print(f"Error processing message: {e}")
            import traceback
            traceback.print_exc()
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

    channel.basic_consume(queue=queue_name, on_message_callback=on_message)
    print(f"Consuming from queue: {queue_name} (exchange={exchange}, rk={routing_key})")
    channel.start_consuming()
