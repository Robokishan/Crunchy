from django.core.management import BaseCommand
from rabbitmq.apps import RabbitMQManager
from databucket.models import Crunchbase
from databucket.serializer import CrunchbaseSerializer
from tqdm import tqdm


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--url', type=str, help='Crunchbase URL', required=False)

    def handle(self, *args, **options):
        crunchbase_url = options['url']
        RabbitMQManager.connect_to_rabbitmq()
        if crunchbase_url is None:
            queryset = Crunchbase.objects.filter(funding_usd__isnull=True).order_by("-updated_at")
            total = queryset.count()
            for company in tqdm(queryset, total=total, ascii=' ='):
                serialized_data = CrunchbaseSerializer(company).data
                del serialized_data['_id']
                stocksymbol = serialized_data.get('stocksymbol')
                del serialized_data['stocksymbol']
                serialized_data['stock_symbol'] = stocksymbol
                RabbitMQManager.publish_crunchbase_item(serialized_data)
        else:
            company = Crunchbase.objects.get(crunchbase_url=crunchbase_url)
            serialized_data = CrunchbaseSerializer(company).data
            del serialized_data['_id']
            stocksymbol = serialized_data.get('stocksymbol')
            del serialized_data['stocksymbol']
            serialized_data['stock_symbol'] = stocksymbol
            print(serialized_data)
            RabbitMQManager.publish_crunchbase_item(serialized_data)
