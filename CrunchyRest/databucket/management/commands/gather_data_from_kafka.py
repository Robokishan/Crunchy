from django.core.management import BaseCommand
from rabbitmq.apps import RabbitMQManager
from databucket.models import Crunchbase
from kafka.consumer import Subscriber


class Command(BaseCommand):
    def handle(self, *args, **options):
        subscriber = Subscriber(callback=self.callback)
        subscriber.connect()
        subscriber.run()

    def callback(self, data):
        try:
            crunchbase, created = Crunchbase.objects.update_or_create(
                crunchbase_url=data['crunchbase_url'],
                defaults={
                    'name': data.get('name'),
                    'funding': data.get('funding'),
                    'website': data.get('website'),
                    'logo': data.get('logo'),
                    'founders': data.get('founders', []),
                    'similar_companies': data.get('similar_companies', []),
                    'description': data.get('description'),
                    'long_description': data.get('long_description'),
                    'acquired': data.get('acquired'),
                    'industries': data.get('industries', []),
                    'founded': data.get('founded'),
                    'lastfunding': data.get('lastfunding'),
                    'stocksymbol': data.get('stock_symbol')

                }
            )
            print("Created:", crunchbase, created, data)
            if data.get('similar_companies'):
                for company in data['similar_companies']:
                    try:
                        isFound = Crunchbase.objects.get(
                            crunchbase_url=company)
                        print("Company already found", isFound, company)
                    except Exception as e:
                        # this company didn't found in database
                        print("sending company back to queue", company)
                        RabbitMQManager.publish_message(company)
            return True
        except Exception as e:
            print("Error", e)
            return False
