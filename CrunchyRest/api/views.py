from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import serializers
from rabbitmq.apps import RabbitMQManager


def is_crunchbase_url(url):
    return bool(url and "crunchbase.com" in url)


def is_tracxn_url(url):
    return bool(url and "tracxn.com" in url)


class CrawlSerializer(serializers.Serializer):
    url = serializers.ListSerializer(child=serializers.URLField())


@api_view(['POST'])
def createCrawl(request):
    serializer = CrawlSerializer(data=request.data)
    try:
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)
        urls = serializer.validated_data['url']
        invalid = [u for u in urls if not is_crunchbase_url(u) and not is_tracxn_url(u)]
        if invalid:
            return Response(
                {"error": "URL must be a Crunchbase or Tracxn URL.", "invalid_urls": invalid},
                status=400,
            )
        for url in urls:
            entry_point = "crunchbase" if is_crunchbase_url(url) else "tracxn"
            message = {"url": url, "entry_point": entry_point}
            if entry_point == "crunchbase":
                RabbitMQManager.publish_crunchbase_crawl(message)
            else:
                RabbitMQManager.publish_tracxn_crawl(message)
        return Response("Sent")
    except Exception as e:
        print(e)
        return Response("Something went wrong", status=400)
