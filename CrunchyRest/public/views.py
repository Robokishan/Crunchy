from collections import defaultdict
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


def get_industries_by_total_funding(base_query, funding_min=None, funding_max=None):
    pipeline = [
        {'$match': base_query or {}},
        {'$unwind': '$industries'},
        {
            '$group': {
                '_id': '$industries',
                'total_funding_usd': {'$sum': '$funding_usd'},
            }
        },
    ]

    eligible_industries = []
    for row in Crunchbase.objects.mongo_aggregate(pipeline):
        total_funding_usd = row.get('total_funding_usd') or 0
        if total_funding_usd <= 0:
            continue
        if funding_min is not None and total_funding_usd < funding_min:
            continue
        if funding_max is not None and total_funding_usd > funding_max:
            continue
        industry = row.get('_id')
        if industry:
            eligible_industries.append(industry)
    return eligible_industries


FUNDING_BRACKETS = (
    {
        'key': 'under_50k',
        'label': 'Under $50K',
        'min': 0,
        'max': 50_000,
    },
    {
        'key': '50k_to_100k',
        'label': '$50K-$100K',
        'min': 50_000,
        'max': 100_000,
    },
    {
        'key': '100k_to_150k',
        'label': '$100K-$150K',
        'min': 100_000,
        'max': 150_000,
    },
    {
        'key': '150k_to_250k',
        'label': '$150K-$250K',
        'min': 150_000,
        'max': 250_000,
    },
    {
        'key': '250k_to_400k',
        'label': '$250K-$400K',
        'min': 250_000,
        'max': 400_000,
    },
    {
        'key': '400k_to_600k',
        'label': '$400K-$600K',
        'min': 400_000,
        'max': 600_000,
    },
    {
        'key': '600k_to_850k',
        'label': '$600K-$850K',
        'min': 600_000,
        'max': 850_000,
    },
    {
        'key': '850k_to_1m',
        'label': '$850K-$1M',
        'min': 850_000,
        'max': 1_000_000,
    },
    {
        'key': '1m_to_1_5m',
        'label': '$1M-$1.5M',
        'min': 1_000_000,
        'max': 1_500_000,
    },
    {
        'key': '1_5m_to_2m',
        'label': '$1.5M-$2M',
        'min': 1_500_000,
        'max': 2_000_000,
    },
    {
        'key': '2m_to_3m',
        'label': '$2M-$3M',
        'min': 2_000_000,
        'max': 3_000_000,
    },
    {
        'key': '3m_to_5m',
        'label': '$3M-$5M',
        'min': 3_000_000,
        'max': 5_000_000,
    },
    {
        'key': '5m_to_7_5m',
        'label': '$5M-$7.5M',
        'min': 5_000_000,
        'max': 7_500_000,
    },
    {
        'key': '7_5m_to_10m',
        'label': '$7.5M-$10M',
        'min': 7_500_000,
        'max': 10_000_000,
    },
    {
        'key': '10m_to_15m',
        'label': '$10M-$15M',
        'min': 10_000_000,
        'max': 15_000_000,
    },
    {
        'key': '15m_to_20m',
        'label': '$15M-$20M',
        'min': 15_000_000,
        'max': 20_000_000,
    },
    {
        'key': '20m_to_25m',
        'label': '$20M-$25M',
        'min': 20_000_000,
        'max': 25_000_000,
    },
    {
        'key': '25m_to_35m',
        'label': '$25M-$35M',
        'min': 25_000_000,
        'max': 35_000_000,
    },
    {
        'key': '35m_to_50m',
        'label': '$35M-$50M',
        'min': 35_000_000,
        'max': 50_000_000,
    },
    {
        'key': '50m_to_75m',
        'label': '$50M-$75M',
        'min': 50_000_000,
        'max': 75_000_000,
    },
    {
        'key': '75m_to_100m',
        'label': '$75M-$100M',
        'min': 75_000_000,
        'max': 100_000_000,
    },
    {
        'key': '100m_to_150m',
        'label': '$100M-$150M',
        'min': 100_000_000,
        'max': 150_000_000,
    },
    {
        'key': '150m_to_250m',
        'label': '$150M-$250M',
        'min': 150_000_000,
        'max': 250_000_000,
    },
    {
        'key': '250m_to_350m',
        'label': '$250M-$350M',
        'min': 250_000_000,
        'max': 350_000_000,
    },
    {
        'key': '350m_to_500m',
        'label': '$350M-$500M',
        'min': 350_000_000,
        'max': 500_000_000,
    },
    {
        'key': '500m_to_750m',
        'label': '$500M-$750M',
        'min': 500_000_000,
        'max': 750_000_000,
    },
    {
        'key': '750m_to_1b',
        'label': '$750M-$1B',
        'min': 750_000_000,
        'max': 1_000_000_000,
    },
    {
        'key': '1b_to_2b',
        'label': '$1B-$2B',
        'min': 1_000_000_000,
        'max': 2_000_000_000,
    },
    {
        'key': '2b_to_5b',
        'label': '$2B-$5B',
        'min': 2_000_000_000,
        'max': 5_000_000_000,
    },
    {
        'key': '5b_plus',
        'label': '$5B+',
        'min': 5_000_000_000,
        'max': None,
    },
)


def get_funding_bracket_meta(funding_usd):
    if not isinstance(funding_usd, (int, float)) or funding_usd <= 0:
        return None

    for bracket in FUNDING_BRACKETS:
        min_value = bracket['min']
        max_value = bracket['max']
        if funding_usd < min_value:
            continue
        if max_value is None or funding_usd < max_value:
            return bracket
    return FUNDING_BRACKETS[-1]


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
        aggregate_funding_filter = None
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
                elif filter["id"] == "aggregate_funding_usd":
                    try:
                        raw_value = filter.get("value", [])
                        aggregate_funding_filter = [
                            int(v) if v is not None and v != "" else None for v in raw_value
                        ]
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
            if aggregate_funding_filter is not None:
                eligible_industries = get_industries_by_total_funding(
                    root_query,
                    funding_min=aggregate_funding_filter[0],
                    funding_max=aggregate_funding_filter[1],
                )
                industry_query = build_industry_query(eligible_industries, 'any')
                if industry_query:
                    root_query.setdefault('$and', []).append(industry_query)
                else:
                    root_query = {'_id': {'$in': []}}
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
        analyticsMode = serializers.ChoiceField(
            choices=['legacy', 'industry_total'],
            required=False,
        )
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
        analytics_mode = request.GET.get('analyticsMode', 'legacy')
        if analytics_mode not in ('legacy', 'industry_total'):
            analytics_mode = 'legacy'
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
            'analytics_mode': analytics_mode,
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
        analytics_mode='legacy',
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

        if analytics_mode == 'legacy':
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

        if analytics_mode == 'legacy':
            filters.extend([
                {'funding_usd': {'$ne': None}},
                {'funding_usd': {'$gt': 0}},
                {'industries': {'$exists': True, '$ne': []}},
            ])
        else:
            filters.extend([
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
        analytics_mode='legacy',
        industry_groups=None,
        industry_group_operator='any',
        excluded_industries=None,
    ):
        match_query = cls.build_match_query(
            search=search,
            funding_min=funding_min,
            funding_max=funding_max,
            analytics_mode=analytics_mode,
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
                    'total_funding_usd': {'$sum': '$funding_usd'},
                }
            },
        ]

        results = []
        for row in Crunchbase.objects.mongo_aggregate(pipeline):
            values = sorted(
                value for value in row.get('funding_values', [])
                if isinstance(value, (int, float)) and value > 0
            )
            total_funding_usd = float(row.get('total_funding_usd') or 0)
            if analytics_mode == 'legacy' and not values:
                continue
            if analytics_mode == 'industry_total':
                if total_funding_usd <= 0:
                    continue
                if funding_min is not None and total_funding_usd < funding_min:
                    continue
                if funding_max is not None and total_funding_usd > funding_max:
                    continue
            results.append({
                'industry': row.get('_id'),
                'company_count': row.get('company_count', 0),
                'median_funding_usd': float(median(values)) if values else 0.0,
                'total_funding_usd': total_funding_usd,
            })

        results.sort(
            key=lambda item: (
                item['total_funding_usd']
                if analytics_mode == 'industry_total'
                else item['median_funding_usd'],
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
            'metric': 'total_funding_usd'
            if applied_filters['analytics_mode'] == 'industry_total'
            else 'median_funding_usd',
            'results': results,
            'applied_filters': {
                'search': applied_filters['search'],
                'fundingMin': applied_filters['funding_min'],
                'fundingMax': applied_filters['funding_max'],
                'analyticsMode': applied_filters['analytics_mode'],
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


class FundingBracketDistributionView(generics.GenericAPIView):
    @staticmethod
    def _clean_industries(industries):
        cleaned = [
            industry.strip()
            for industry in (industries or [])
            if isinstance(industry, str) and industry.strip()
        ]
        return list(dict.fromkeys(cleaned))

    @staticmethod
    def _coerce_funding(value):
        try:
            funding_usd = float(value)
        except (TypeError, ValueError):
            return None
        if funding_usd <= 0:
            return None
        return funding_usd

    @classmethod
    def _empty_bracket_state(cls):
        return {
            bracket['key']: {
                'company_count': 0,
                'total_funding_usd': 0.0,
                'funding_values': [],
                'industries': defaultdict(
                    lambda: {'industry': '', 'company_count': 0, 'total_funding_usd': 0.0}
                ),
            }
            for bracket in FUNDING_BRACKETS
        }

    @classmethod
    def _build_payload(cls):
        summary = {
            'total_companies': 0,
            'funded_companies': 0,
            'bracketed_companies': 0,
            'excluded_without_funding': 0,
            'excluded_without_industries': 0,
            'total_funding_usd': 0.0,
            'coverage_ratio': 0.0,
        }
        bracket_state = cls._empty_bracket_state()

        options = CodecOptions(document_class=dict)
        cursor = Crunchbase.objects.mongo_with_options(codec_options=options).find(
            {},
            {
                'industries': 1,
                'funding_usd': 1,
            },
        )

        for doc in cursor:
            summary['total_companies'] += 1
            industries = cls._clean_industries(doc.get('industries', []))
            funding_usd = cls._coerce_funding(doc.get('funding_usd'))

            if funding_usd is None:
                summary['excluded_without_funding'] += 1
            else:
                summary['funded_companies'] += 1
                summary['total_funding_usd'] += funding_usd

            if funding_usd is not None and not industries:
                summary['excluded_without_industries'] += 1

            if funding_usd is None or not industries:
                continue

            bracket = get_funding_bracket_meta(funding_usd)
            if bracket is None:
                continue

            summary['bracketed_companies'] += 1
            state = bracket_state[bracket['key']]
            state['company_count'] += 1
            state['total_funding_usd'] += funding_usd
            state['funding_values'].append(funding_usd)

            for industry in industries:
                industry_row = state['industries'][industry]
                industry_row['industry'] = industry
                industry_row['company_count'] += 1
                industry_row['total_funding_usd'] += funding_usd

        if summary['funded_companies'] > 0:
            summary['coverage_ratio'] = (
                summary['bracketed_companies'] / summary['funded_companies']
            )

        brackets = []
        for bracket in FUNDING_BRACKETS:
            state = bracket_state[bracket['key']]
            industries = list(state['industries'].values())
            industries.sort(
                key=lambda item: (
                    item['company_count'],
                    item['total_funding_usd'],
                    item['industry'],
                ),
                reverse=True,
            )

            brackets.append({
                'key': bracket['key'],
                'label': bracket['label'],
                'min': bracket['min'],
                'max': bracket['max'],
                'company_count': state['company_count'],
                'industry_count': len(industries),
                'total_funding_usd': float(state['total_funding_usd']),
                'median_funding_usd': float(median(state['funding_values']))
                if state['funding_values']
                else 0.0,
                'share_of_funded_companies': (
                    state['company_count'] / summary['funded_companies']
                    if summary['funded_companies'] > 0
                    else 0.0
                ),
                'industries': [
                    {
                        'industry': item['industry'],
                        'company_count': item['company_count'],
                        'total_funding_usd': float(item['total_funding_usd']),
                    }
                    for item in industries
                ],
            })

        return {
            'summary': {
                **summary,
                'total_funding_usd': float(summary['total_funding_usd']),
            },
            'brackets': brackets,
        }

    def list(self, request, *args, **kwargs):
        return Response(self._build_payload())

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)


class IndustryOverviewAnalyticsView(generics.GenericAPIView):
    class QuerySerializer(serializers.Serializer):
        topN = serializers.IntegerField(required=False, min_value=5, max_value=200)

    @staticmethod
    def _parse_top_n(request):
        try:
            top_n = int(request.GET.get('topN', 50))
        except (TypeError, ValueError):
            top_n = 50
        return max(5, min(top_n, 200))

    @classmethod
    def _get_company_count_distribution(cls, top_n):
        pipeline = [
            {'$match': {'industries': {'$exists': True, '$ne': []}}},
            {'$unwind': '$industries'},
            {
                '$group': {
                    '_id': '$industries',
                    'company_count': {'$sum': 1},
                }
            },
        ]

        results = []
        for row in Crunchbase.objects.mongo_aggregate(pipeline):
            industry = row.get('_id')
            company_count = row.get('company_count', 0)
            if not industry or company_count <= 0:
                continue
            results.append({
                'industry': industry,
                'company_count': company_count,
            })

        results.sort(
            key=lambda item: (item['company_count'], item['industry']),
            reverse=True,
        )
        return results[:top_n]

    @classmethod
    def _get_total_funding_distribution(cls, top_n):
        pipeline = [
            {'$match': {'funding_usd': {'$gt': 0}, 'industries': {'$exists': True, '$ne': []}}},
            {'$unwind': '$industries'},
            {
                '$group': {
                    '_id': '$industries',
                    'total_funding_usd': {'$sum': '$funding_usd'},
                    'company_count': {'$sum': 1},
                }
            },
        ]

        results = []
        for row in Crunchbase.objects.mongo_aggregate(pipeline):
            industry = row.get('_id')
            total_funding_usd = float(row.get('total_funding_usd') or 0)
            company_count = row.get('company_count', 0)
            if not industry or total_funding_usd <= 0:
                continue
            results.append({
                'industry': industry,
                'total_funding_usd': total_funding_usd,
                'company_count': company_count,
            })

        results.sort(
            key=lambda item: (item['total_funding_usd'], item['industry']),
            reverse=True,
        )
        return results[:top_n]

    @classmethod
    def _get_summary(cls):
        company_count_pipeline = [
            {
                '$group': {
                    '_id': None,
                    'total_companies': {'$sum': 1},
                    'funded_companies': {
                        '$sum': {
                            '$cond': [{'$gt': ['$funding_usd', 0]}, 1, 0]
                        }
                    },
                    'total_funding_usd': {'$sum': '$funding_usd'},
                }
            }
        ]
        company_stats = next(iter(Crunchbase.objects.mongo_aggregate(company_count_pipeline)), {})

        industry_count_pipeline = [
            {'$match': {'industries': {'$exists': True, '$ne': []}}},
            {'$unwind': '$industries'},
            {'$group': {'_id': '$industries'}},
            {'$group': {'_id': None, 'total_industries': {'$sum': 1}}},
        ]
        industry_stats = next(iter(Crunchbase.objects.mongo_aggregate(industry_count_pipeline)), {})

        return {
            'total_companies': company_stats.get('total_companies', 0),
            'funded_companies': company_stats.get('funded_companies', 0),
            'total_funding_usd': float(company_stats.get('total_funding_usd') or 0),
            'total_industries': industry_stats.get('total_industries', 0),
        }

    def list(self, request, *args, **kwargs):
        top_n = self._parse_top_n(request)
        serializer = self.QuerySerializer(data={'topN': top_n})
        serializer.is_valid(raise_exception=True)

        payload = {
            'summary': self._get_summary(),
            'topN': top_n,
            'industry_by_company_count': self._get_company_count_distribution(top_n),
            'industry_by_total_funding': self._get_total_funding_distribution(top_n),
        }
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
