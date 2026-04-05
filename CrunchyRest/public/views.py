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
from statistics import median


def build_industry_query(industries, operator='all'):
    cleaned_industries = [
        industry.strip()
        for industry in (industries or [])
        if isinstance(industry, str) and industry.strip()
    ]
    if not cleaned_industries:
        return None

    clauses = [
        {'industries': {'$regex': f'^{re.escape(industry)}$', '$options': 'i'}}
        for industry in cleaned_industries
    ]

    if operator == 'any':
        return {'$or': clauses}
    if len(clauses) == 1:
        return clauses[0]
    return {'$and': clauses}


def normalize_industry_groups(industry_groups):
    normalized_groups = []
    for group in industry_groups or []:
        if not isinstance(group, dict):
            continue
        operator = group.get('operator', 'any')
        if operator not in ('any', 'all'):
            operator = 'any'
        industries = [
            industry.strip()
            for industry in group.get('industries', [])
            if isinstance(industry, str) and industry.strip()
        ]
        if not industries:
            continue
        normalized_groups.append({
            'operator': operator,
            'industries': list(dict.fromkeys(industries)),
        })
    return normalized_groups


def build_industry_groups_query(industry_groups, operator='all'):
    normalized_groups = normalize_industry_groups(industry_groups)
    if not normalized_groups:
        return None

    clauses = []
    for group in normalized_groups:
        clause = build_industry_query(group['industries'], group['operator'])
        if clause:
            clauses.append(clause)

    if not clauses:
        return None
    if len(clauses) == 1:
        return clauses[0]
    if operator == 'any':
        return {'$or': clauses}
    return {'$and': clauses}


def build_excluded_industries_query(industries):
    cleaned_industries = [
        industry.strip()
        for industry in (industries or [])
        if isinstance(industry, str) and industry.strip()
    ]
    if not cleaned_industries:
        return None

    return {
        '$nor': [
            {'industries': {'$regex': f'^{re.escape(industry)}$', '$options': 'i'}}
            for industry in list(dict.fromkeys(cleaned_industries))
        ]
    }


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

    @staticmethod
    def _crunchbase_doc_to_company_shape(doc):
        """Normalize a Crunchbase document (dict) to Company-shaped keys for CompanySerializer."""
        if not isinstance(doc, dict):
            return doc

        funding_usd = doc.get('funding_usd')
        if funding_usd is None:
            funding_usd = doc.get('funding_total_usd', 0)

        funding = doc.get('funding')
        if funding is None:
            funding = doc.get('funding_total')

        lastfunding = doc.get('lastfunding')

        return {
            **doc,
            'funding': funding,
            'funding_usd': funding_usd,
            'funding_total': doc.get('funding_total', funding),
            'funding_rounds': doc.get('funding_rounds', []),
            'sources': doc.get('sources', ['crunchbase']),
            'source_priority': doc.get('source_priority', {}),
            'funding_total_usd': doc.get('funding_total_usd', funding_usd),
            'lastfunding': lastfunding,
            'match_confidence': doc.get('match_confidence', 1.0),
        }

    def _serialize_companies(self, companies):
        serializer = self.get_serializer(companies, many=True)
        # Ensure normalized funding keys are always present in API payload.
        data = [dict(item) for item in serializer.data]
        for idx, item in enumerate(data):
            item.pop('last_funding_date', None)
            item.pop('last_funding_type', None)
            source = companies[idx] if idx < len(companies) else {}
            if not isinstance(source, dict):
                continue
            item['funding'] = source.get('funding')
            item['funding_usd'] = source.get('funding_usd')
            item['lastfunding'] = source.get('lastfunding')
        return data

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            page = [self._crunchbase_doc_to_company_shape(d) for d in page]
            data = self._serialize_companies(page)
            return self.get_paginated_response(data)
        page = [self._crunchbase_doc_to_company_shape(d) for d in queryset]
        return Response(self._serialize_companies(page))

    @staticmethod
    def build_root_query(filters=None, globalFilter=None):
        root_query = {}
        mongo_query = []
        if globalFilter != 'null' and globalFilter is not None:
            mongo_query = [
                {'name': {'$regex': globalFilter, '$options': 'i'}},
                {'description': {'$regex': globalFilter, '$options': 'i'}},
                {'long_description': {'$regex': globalFilter, '$options': 'i'}},
                {'founders': {'$regex': globalFilter, '$options': 'i'}},
                {'website': {'$regex': globalFilter, '$options': 'i'}}
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
                    industry_query = build_industry_query(
                        industries,
                        filter.get("operator", "all"),
                    )
                    if industry_query:
                        mongo_query.append(industry_query)
                elif filter["id"] == "industry_groups":
                    industry_groups_query = build_industry_groups_query(
                        filter.get("groups", []),
                        filter.get("operator", "all"),
                    )
                    if industry_groups_query:
                        mongo_query.append(industry_groups_query)
                elif filter["id"] == "excluded_industries":
                    excluded_industries_query = build_excluded_industries_query(
                        filter.get("value", []),
                    )
                    if excluded_industries_query:
                        mongo_query.append(excluded_industries_query)
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
                                '$or': [
                                    {'funding_usd': {'$gte': filter["value"][0]}},
                                    {'funding_total_usd': {'$gte': filter["value"][0]}},
                                ]
                            })

                        if filter["value"][1] is not None:
                            mongo_query.append({
                                '$or': [
                                    {'funding_usd': {'$lte': filter["value"][1]}},
                                    {'funding_total_usd': {'$lte': filter["value"][1]}},
                                ]
                            })
                    except ValueError as e:
                        print(e)
                elif filter["id"] == "funding":
                    mongo_query.append({
                        '$or': [
                            {'funding': {'$regex': filter["value"], '$options': 'i'}},
                            {'funding_total': {'$regex': filter["value"], '$options': 'i'}},
                        ]
                    })
            if len(mongo_query) > 0:
                root_query['$and'] = mongo_query
        return root_query

    @staticmethod
    def build_sort(sorting=None):
        sort = []
        if sorting:
            sorting = json.loads(sorting) if isinstance(sorting, str) else sorting
            for sort_field in sorting:
                field = sort_field["id"]
                direction = -1 if sort_field.get("desc", False) else 1
                if field == "funding_usd":
                    sort.append(("funding_usd", direction))
                elif field == "funding":
                    sort.append(("funding_usd", direction))
                else:
                    sort.append((field, direction))
        return sort

    def get_queryset(self):
        filters = self.request.GET.get('filters', None)
        sorting = self.request.GET.get('sorting', None)
        globalFilter = self.request.GET.get('search', None)

        root_query = self.build_root_query(filters=filters, globalFilter=globalFilter)

        sort = self.build_sort(sorting=sorting)

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
        interested_industries = InterestedIndustries.get_interested_industries()

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

    def get_queryset(self, selected: list, sortBy: str = 'default'):

        all_filter = []

        # check if selected is array
        if isinstance(selected, list) and len(selected) > 0:
            for industry in selected:
                if industry != '':
                    all_filter.append(
                        {'$elemMatch': {'$regex': f"^{re.escape(industry)}$", '$options': "i"}}),

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

            for i, f in enumerate(filter):
                if '$sort' in f:
                    if sortBy == 'industryCount':
                        filter[i]['$sort'] = {
                            'count': -1
                        }
                    elif sortBy == 'alphabetical':
                        filter[i]['$sort'] = {
                            '_id': 1
                        }

        industries = Crunchbase.objects.mongo_aggregate(filter)
        return list(industries)

    def list(self, request, *args, **kwargs):
        selected = request.GET.getlist('selected[]', [])
        sortBy = request.GET.get('sortBy', 'default')

        return Response(self.get_queryset(selected, sortBy))


class IndustryFundingAnalyticsView(generics.GenericAPIView):
    class QuerySerializer(serializers.Serializer):
        search = serializers.CharField(required=False, allow_blank=True)
        fundingMin = serializers.FloatField(required=False, allow_null=True)
        fundingMax = serializers.FloatField(required=False, allow_null=True)
        industryGroupOperator = serializers.ChoiceField(
            choices=['any', 'all'],
            required=False,
        )
        industryGroups = serializers.ListField(
            child=serializers.DictField(), required=False
        )
        excludedIndustries = serializers.ListField(
            child=serializers.CharField(), required=False
        )

    @staticmethod
    def _coerce_float(value):
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @classmethod
    def _get_query_filters(cls, request):
        search = (request.GET.get('search', '') or '').strip()
        funding_min = cls._coerce_float(request.GET.get('fundingMin'))
        funding_max = cls._coerce_float(request.GET.get('fundingMax'))
        industry_group_operator = request.GET.get('industryGroupOperator', 'any')
        if industry_group_operator not in ('any', 'all'):
            industry_group_operator = 'any'
        raw_industry_groups = request.GET.get('industryGroups')
        industry_groups = []
        if raw_industry_groups:
            try:
                industry_groups = normalize_industry_groups(json.loads(raw_industry_groups))
            except (TypeError, ValueError, json.JSONDecodeError):
                industry_groups = []
        if not industry_groups:
            fallback_industries = [
                industry.strip()
                for industry in request.GET.getlist('industries[]', [])
                if industry and industry.strip()
            ]
            if fallback_industries:
                industry_groups = [{
                    'operator': request.GET.get('industryMode', 'any')
                    if request.GET.get('industryMode', 'any') in ('any', 'all')
                    else 'any',
                    'industries': list(dict.fromkeys(fallback_industries)),
                }]
        raw_excluded_industries = request.GET.get('excludedIndustries')
        excluded_industries = []
        if raw_excluded_industries:
            try:
                excluded_industries = [
                    industry.strip()
                    for industry in json.loads(raw_excluded_industries)
                    if isinstance(industry, str) and industry.strip()
                ]
            except (TypeError, ValueError, json.JSONDecodeError):
                excluded_industries = []
        return {
            'search': search,
            'funding_min': funding_min,
            'funding_max': funding_max,
            'industry_group_operator': industry_group_operator,
            'industry_groups': industry_groups,
            'excluded_industries': list(dict.fromkeys(excluded_industries)),
        }

    @classmethod
    def build_match_query(
        cls,
        search='',
        funding_min=None,
        funding_max=None,
        industry_groups=None,
        industry_group_operator='any',
        excluded_industries=None,
    ):
        filters = []
        if search:
            filters.append({
                '$or': [
                    {'name': {'$regex': search, '$options': 'i'}},
                    {'description': {'$regex': search, '$options': 'i'}},
                    {'long_description': {'$regex': search, '$options': 'i'}},
                    {'founders': {'$regex': search, '$options': 'i'}},
                    {'website': {'$regex': search, '$options': 'i'}},
                ]
            })

        if funding_min is not None:
            filters.append({'funding_usd': {'$gte': funding_min}})
        if funding_max is not None:
            filters.append({'funding_usd': {'$lte': funding_max}})

        industry_query = build_industry_groups_query(
            industry_groups,
            industry_group_operator,
        )
        if industry_query:
            filters.append(industry_query)

        excluded_industries_query = build_excluded_industries_query(excluded_industries)
        if excluded_industries_query:
            filters.append(excluded_industries_query)

        filters.extend([
            {'funding_usd': {'$ne': None}},
            {'funding_usd': {'$gt': 0}},
            {'industries': {'$exists': True, '$ne': []}},
        ])

        if not filters:
            return {}
        if len(filters) == 1:
            return filters[0]
        return {'$and': filters}

    @classmethod
    def get_queryset(
        cls,
        search='',
        funding_min=None,
        funding_max=None,
        industry_groups=None,
        industry_group_operator='any',
        excluded_industries=None,
    ):
        match_query = cls.build_match_query(
            search=search,
            funding_min=funding_min,
            funding_max=funding_max,
            industry_groups=industry_groups,
            industry_group_operator=industry_group_operator,
            excluded_industries=excluded_industries,
        )
        pipeline = [
            {'$match': match_query},
            {'$unwind': '$industries'},
            {
                '$group': {
                    '_id': '$industries',
                    'company_count': {'$sum': 1},
                    'funding_values': {'$push': '$funding_usd'},
                }
            },
        ]

        results = []
        for row in Crunchbase.objects.mongo_aggregate(pipeline):
            values = sorted(
                value for value in row.get('funding_values', [])
                if isinstance(value, (int, float)) and value > 0
            )
            if not values:
                continue
            results.append({
                'industry': row.get('_id'),
                'company_count': row.get('company_count', 0),
                'median_funding_usd': float(median(values)),
            })

        results.sort(
            key=lambda item: (
                item['median_funding_usd'],
                item['company_count'],
                item['industry'] or '',
            ),
            reverse=True,
        )
        return results

    def list(self, request, *args, **kwargs):
        applied_filters = self._get_query_filters(request)
        results = self.get_queryset(**applied_filters)
        payload = {
            'metric': 'median_funding_usd',
            'results': results,
            'applied_filters': {
                'search': applied_filters['search'],
                'fundingMin': applied_filters['funding_min'],
                'fundingMax': applied_filters['funding_max'],
                'industryGroupOperator': applied_filters['industry_group_operator'],
                'industryGroups': applied_filters['industry_groups'],
                'excludedIndustries': applied_filters['excluded_industries'],
            },
        }
        serializer = self.QuerySerializer(data=payload['applied_filters'])
        serializer.is_valid(raise_exception=True)
        return Response(payload)

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)


@ api_view(['GET'])
def PendingInQueue(request):
    crunchbase_pending = RabbitMQManager.get_pending_in_crunchbase_crawl_queue()
    tracxn_pending = RabbitMQManager.get_pending_in_tracxn_crawl_queue()
    return Response({
        "crunchbase": crunchbase_pending if crunchbase_pending is not None else 0,
        "tracxn": tracxn_pending if tracxn_pending is not None else 0,
    })
