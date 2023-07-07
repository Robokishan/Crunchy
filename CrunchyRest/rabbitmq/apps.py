import pika
from django.conf import settings
from django.apps import AppConfig
from rabbitmq.manager import RabbitMQManager


class RabbitMQConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'rabbitmq'

    def ready(self):
        # Connect to RabbitMQ upon app initialization
        RabbitMQManager.connect_to_rabbitmq()
