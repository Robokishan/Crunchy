from rest_framework.decorators import api_view
from rest_framework import generics
from rest_framework.response import Response
from databucket.serializer import CrunchbaseSerializer
from databucket.models import Crunchbase
from databucket.models import InterestedIndustries
from django.db.models import Q
from knowledgeGraph import db
from rest_framework import pagination
import json
from rest_framework import serializers
from rabbitmq.apps import RabbitMQManager


class CompanyPagination(pagination.PageNumberPagination):
    page_size = 100
    max_page_size = 300


class CompaniesListView(generics.ListAPIView):
    serializer_class = CrunchbaseSerializer
    pagination_class = CompanyPagination

    def get_queryset(self):
        queryset = Crunchbase.objects.order_by("-updated_at")

        filter_conditions = Q()
        filters = self.request.GET.get('filters', None)
        sorting = self.request.GET.get('sorting', None)
        globalFilter = self.request.GET.get('search', None)

        if globalFilter != 'null' and globalFilter != None:
            queryset = queryset.filter(
                Q(name__icontains=globalFilter) |
                Q(description__icontains=globalFilter) |
                Q(founders__icontains=globalFilter)
            )
        elif filters:
            filters = json.loads(filters)
            # filters: [{"id":"name","value":"level ai"}]
            for filter in filters:
                if filter["id"] == "name":
                    filter_conditions &= Q(name__icontains=filter["value"])
                elif filter["id"] == "description":
                    filter_conditions &= Q(
                        description__icontains=filter["value"])
                elif filter["id"] == "industries":
                    filter_conditions &= Q(
                        industries__icontains=filter["value"])
                elif filter["id"] == "lastfunding":
                    filter_conditions &= Q(
                        lastfunding__icontains=filter["value"])
                elif filter["id"] == "website":
                    filter_conditions &= Q(website__icontains=filter["value"])
                elif filter["id"] == "funding_usd":
                    try:
                        filter["value"] = [
                            int(v) if v is not None and v != "" else None for v in filter["value"]]
                        # value will be ["10",null] first element is gte and second element is lte
                        if filter["value"][0] != None:
                            filter_conditions &= Q(
                                funding_usd__gte=filter["value"][0])
                        if filter["value"][1] != None:
                            filter_conditions &= Q(
                                funding_usd__lte=filter["value"][1])
                    except ValueError as e:
                        print(e)

            if len(filters) > 0:
                queryset = queryset.filter(filter_conditions)

        if sorting:
            sorting = json.loads(sorting)
            sort_fields = []
            for sort in sorting:
                field = sort["id"]
                if sort.get("desc", False):  # Check if 'desc' key exists and is True
                    field = f"-{field}"
                sort_fields.append(field)
            if len(sorting) > 0:
                queryset = queryset.order_by(*sort_fields)

        return queryset


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


@api_view(['GET'])
def PendingInQueue(request):
    priorityPending_messages = RabbitMQManager.get_pending_in_priority_queue()
    normalPending_messages = RabbitMQManager.get_pending_in_normal_queue()

    if priorityPending_messages is None:
        priorityPending_messages = 0

    if normalPending_messages is None:
        normalPending_messages = 0

    return Response({"priority": priorityPending_messages, "normal": normalPending_messages})
