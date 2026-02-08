from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import serializers
from rabbitmq.apps import RabbitMQManager


class CrawlSerializer(serializers.Serializer):
    url = serializers.ListSerializer(child=serializers.URLField())


@api_view(['POST'])
def createCrawl(request):
    serializer = CrawlSerializer(data=request.data)
    try:
        if serializer.is_valid():
            urls = serializer.validated_data['url']
            for url in urls:
                entry_point = "crunchbase" if "crunchbase.com" in url else "tracxn"
                message = {"url": url, "entry_point": entry_point}
                print('URL Sent to RabbitMQ', message)
                if entry_point == "crunchbase":
                    RabbitMQManager.publish_crunchbase_crawl(message)
                else:
                    RabbitMQManager.publish_tracxn_crawl(message)
            return Response("Sent")
        else:
            return Response(serializer.errors, status=400)
    except Exception as e:
        print(e)
        return Response("Something went wrong", status=400)
