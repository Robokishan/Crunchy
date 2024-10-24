from rest_framework.decorators import api_view
from rest_framework import generics
from rest_framework.response import Response
from databucket.serializer import CompanySerializer
from databucket.models import Crunchbase
from databucket.models import InterestedIndustries
from django.db.models import Q
from knowledgeGraph import db
from rest_framework import pagination
import json
from rest_framework import serializers
from rabbitmq.apps import RabbitMQManager
from bson.codec_options import CodecOptions
import regex as re
from django.core.paginator import Paginator as DjangoPaginator
from django.utils.functional import cached_property


class CustomDjangoPaginator(DjangoPaginator):
    @cached_property
    def count(self):
        return self.object_list.count()


class CompanyPagination(pagination.PageNumberPagination):
    page_size = 100
    max_page_size = 300

    django_paginator_class = CustomDjangoPaginator


class CompaniesListView(generics.ListAPIView):
    serializer_class = CompanySerializer
    pagination_class = CompanyPagination

    def get_queryset(self):

        filters = self.request.GET.get('filters', None)
        sorting = self.request.GET.get('sorting', None)
        globalFilter = self.request.GET.get('search', None)

        root_query = {}
        mongo_query = []
        if globalFilter != 'null' and globalFilter is not None:
            mongo_query = [
                {'name': {'$regex': globalFilter, '$options': 'i'}},
                {'description': {'$regex': globalFilter, '$options': 'i'}},
                {'founders': {'$regex': globalFilter, '$options': 'i'}}
            ]
            root_query['$or'] = mongo_query
        elif filters:
            filters = json.loads(filters)
            for filter in filters:
                if filter["id"] == "name":
                    mongo_query.append({
                        'name': {'$regex': filter["value"], '$options': 'i'}
                    })
                elif filter["id"] == "description":
                    mongo_query.append({
                        'description': {'$regex': filter["value"], '$options': 'i'}
                    })
                elif filter["id"] == "industries":
                    industries = filter["value"]
                    for industry in industries:
                        mongo_query.append({
                            'industries': {'$regex': f'^{re.escape(industry)}', '$options': 'i'}
                        })
                elif filter["id"] == "lastfunding":
                    mongo_query.append({
                        'lastfunding': {'$regex': filter["value"], '$options': 'i'}
                    })
                elif filter["id"] == "website":
                    mongo_query.append({
                        'website': {'$regex': filter["value"], '$options': 'i'}
                    })
                elif filter["id"] == "crunchbase_url":
                    mongo_query.append({
                        'crunchbase_url': filter["value"]
                    })
                elif filter["id"] == "funding_usd":
                    try:
                        filter["value"] = [
                            int(v) if v is not None and v != "" else None for v in filter["value"]]
                        if filter["value"][0] is not None:
                            mongo_query.append({
                                'funding_usd': {'$gte': filter["value"][0]}
                            })

                        if filter["value"][1] is not None:
                            mongo_query.append({
                                'funding_usd': {'$lte': filter["value"][1]}
                            })
                    except ValueError as e:
                        print(e)
            if len(mongo_query) > 0:
                root_query['$and'] = mongo_query

        sort = []
        if sorting:
            sorting = json.loads(sorting)
            for sort_field in sorting:
                field = sort_field["id"]
                direction = -1 if sort_field.get("desc", False) else 1
                sort.append((field, direction))

        options = CodecOptions(document_class=dict)
        cursor = Crunchbase.objects.mongo_with_options(codec_options=options).find(
            root_query)

        if len(sort) > 0:
            cursor = cursor.sort(sort)

        return cursor


@api_view(['GET'])
def connection(request):
    company = request.GET.get("company", None)
    founder = request.GET.get("founder", None)
    industry = request.GET.get("industry", None)
    key = request.GET.get("key", None)

    if industry and key == "company":
        val = db.get_companies_by_industry(industry)
        return Response(val)
    elif industry and key == "founder":
        val = db.get_founders_by_industry(industry)
        return Response(val)
    elif industry and key == "industry":
        val = db.get_industry_by_industry(industry)
        return Response(val)

    elif founder and key == "company":
        val = db.get_companies_by_founder(founder)
        return Response(val)
    elif founder and key == "founder":
        val = db.get_founders_by_founder(founder)
        return Response(val)
    elif founder and key == "industry":
        val = db.get_industry_by_founder(founder)
        return Response(val)

    elif company and key == "company":
        val = db.get_companies_by_company(company)
        return Response(val)
    elif company and key == "founder":
        val = db.get_founders_by_company(company)
        return Response(val)
    elif company and key == "industry":
        val = db.get_industries_by_company(company)
        return Response(val)

    else:
        return Response("No search query", status=400)


class SettingsList(generics.ListAPIView):
    class IndustrySerializer(serializers.Serializer):
        industries = serializers.ListField(
            child=serializers.CharField()
        )
        interested_industries = serializers.ListField(
            child=serializers.CharField()
        )

    serializer_class = IndustrySerializer

    def get_queryset(self):
        interested_industries = InterestedIndustries.objects.get(
            key="industry").industries

        queryset = Crunchbase.objects.values_list(
            'industries', flat=True).distinct()

        if interested_industries:
            queryset = queryset.exclude(industries__in=[interested_industries])

        # Flatten the list of industries
        industries_list = []
        for industries in queryset:
            if isinstance(industries, list):
                # exclude interested industries
                industries = [
                    industry for industry in industries if industry not in interested_industries]
                industries_list.extend(industries)
            else:
                industries_list.append(industries)

        industries_list = sorted(set(industries_list))
        return industries_list, interested_industries

    def list(self, request, *args, **kwargs):
        queryset, interested_industries = self.get_queryset()
        data = {'industries': queryset,
                'interested_industries': interested_industries}
        serializer = self.get_serializer(data)
        return Response(serializer.data)

    def post(self, request):
        industries = request.data.get("industry", [])
        InterestedIndustries.objects.update_or_create(
            key="industry", defaults={"industries": industries})
        return Response("success")


class IndustryList(generics.ListAPIView):

    def get_queryset(self, selected: list):

        all_filter = []

        # check if selected is array
        if isinstance(selected, list) and len(selected) > 0:
            for industry in selected:
                if industry != '':
                    all_filter.append(
                        {'$elemMatch': {'$regex': f"^{re.escape(industry)}", '$options': "i"}}),

        filter = [
            {
                '$unwind': "$industries"
            },
            {
                '$group': {
                    '_id': "$industries",
                    'count': {'$sum': 1}
                }
            },
            {
                '$sort': {
                    '_id': 1
                }
            },
            {
                '$project': {
                    '_id': 0,
                    'industry': "$_id",
                    'count': "$count"
                }
            }
        ]

        if len(all_filter) > 0:
            filter = [
                {
                    '$match': {
                        'industries': {'$all': all_filter}
                    }
                },
                {
                    '$unwind': "$industries"
                },
                {
                    '$group': {
                        '_id': "$industries",
                        'count': {'$sum': 1}
                    }
                },
                {
                    '$sort': {
                        'count': -1
                    }
                },
                {
                    '$project': {
                        '_id': 0,
                        'industry': "$_id",
                        'count': "$count"
                    }
                }
            ]

        industries = Crunchbase.objects.mongo_aggregate(filter)
        return list(industries)

    def list(self, request, *args, **kwargs):
        selected = request.GET.getlist('selected[]', [])

        return Response(self.get_queryset(selected))


@ api_view(['GET'])
def PendingInQueue(request):
    priorityPending_messages = RabbitMQManager.get_pending_in_priority_queue()
    normalPending_messages = RabbitMQManager.get_pending_in_normal_queue()

    if priorityPending_messages is None:
        priorityPending_messages = 0

    if normalPending_messages is None:
        normalPending_messages = 0

    return Response({"priority": priorityPending_messages, "normal": normalPending_messages})
