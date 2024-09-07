from rest_framework.decorators import api_view
from rest_framework import generics
from rest_framework.response import Response
from databucket.serializer import CrunchbaseSerializer
from databucket.models import Crunchbase
from django.db.models import Q
from knowledgeGraph import db
from rest_framework import pagination
import json
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
                    filter_conditions &= Q(description__icontains=filter["value"])
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