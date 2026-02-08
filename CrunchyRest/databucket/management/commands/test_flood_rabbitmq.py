from django.core.management import BaseCommand
from rabbitmq.apps import RabbitMQManager
from databucket.models import Crunchbase
from django.db.models import Q


class Command(BaseCommand):
    def handle(self, *args, **options):
        queryset = Crunchbase.objects.all().order_by("-updated_at")
        searchText = "artificial"
        queryset = queryset.filter(
            Q(industries__icontains=searchText) |
            Q(description__icontains=searchText) |
            Q(long_description__icontains=searchText) |
            Q(founders__icontains=searchText)
        )

        for index, doc in enumerate(queryset):
            print("Published", doc.name, doc.crunchbase_url, index)
            RabbitMQManager.publish_crunchbase_crawl({"url": doc.crunchbase_url, "entry_point": "flood_test"})
