from django.urls import path
from .views import createCrawl

urlpatterns = [
    path('crawl/create', createCrawl, name="create-crawl"),
]
