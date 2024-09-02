from django.core.management import BaseCommand
from kafka.consumer import Producer
from databucket.models import Crunchbase
from databucket.serializer import CrunchbaseSerializer
import json

class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--url', type=str, help='Crunchbase URL')

    def handle(self, *args, **options):
        crunchbase_url = options['url']
        producer = Producer()
        producer.connect()
        company = Crunchbase.objects.get(
                    crunchbase_url=crunchbase_url)
        serialized_data = CrunchbaseSerializer(
                company).data
        del serialized_data['_id']
        stocksymbol = serialized_data.get('stocksymbol')
        del serialized_data['stocksymbol']
        serialized_data['stock_symbol'] = stocksymbol
        print(serialized_data)
        producer.publish(json.dumps(serialized_data))
    