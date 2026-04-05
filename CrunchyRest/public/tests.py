import json

import pytest
from django.conf import settings
from django.db import connections
from pymongo import MongoClient
from rest_framework.test import APIRequestFactory

from databucket.models import Crunchbase, InterestedIndustries
from public.views import (
    FUNDING_BRACKETS,
    CompaniesListView,
    FundingBracketDistributionView,
    IndustryFundingAnalyticsView,
    IndustryOverviewAnalyticsView,
    SettingsList,
    get_funding_bracket_meta,
)


def create_company(name, industries, funding_usd, created_at=None, **overrides):
    slug = name.lower().replace(" ", "-")
    numeric_funding = funding_usd if isinstance(funding_usd, (int, float)) else 0
    payload = {
        "name": name,
        "funding": f"${numeric_funding}" if numeric_funding else "",
        "funding_usd": funding_usd,
        "rate": 0,
        "website": f"https://{slug}.example.com",
        "crunchbase_url": f"https://crunchbase.com/organization/{slug}",
        "logo": "https://logo.example.com/logo.png",
        "founders": ["Founder"],
        "similar_companies": [],
        "description": f"{name} description",
        "long_description": f"{name} long description",
        "acquired": "",
        "industries": industries,
        "founded": "2020-01-01",
        "lastfunding": "2024-01-01",
        "stocksymbol": "",
    }
    payload.update(overrides)
    company = Crunchbase.objects.create(**payload)
    if created_at is not None:
        company.created_at = created_at
        company.save()
    return company


def company_names(response):
    return [row["name"] for row in response.data["results"]]


def raw_update_company(company, **updates):
    client = MongoClient(settings.DATABASES["default"]["CLIENT"]["host"])
    db_name = connections["default"].settings_dict["NAME"]
    client[db_name][Crunchbase._meta.db_table].update_one(
        {"_id": company._id},
        {"$set": updates},
    )
    client.close()


@pytest.mark.django_db
class TestCompaniesListView:
    def setup_method(self):
        self.factory = APIRequestFactory()
        create_company(
            "Alpha",
            ["AI"],
            10,
            founders=["Alpha Founder"],
            description="Alpha computer vision company",
            long_description="Alpha long description",
            website="https://alpha-ai.example.com",
            lastfunding="2024-03-01",
        )
        create_company(
            "Beta",
            ["Fintech"],
            30,
            founders=["Beta Founder"],
            description="Payments infrastructure",
            long_description="Beta long description",
            website="https://beta-pay.example.com",
            lastfunding="2024-02-01",
        )
        create_company(
            "Gamma",
            ["AI", "Fintech"],
            20,
            founders=["Gamma Founder"],
            description="AI underwriting platform",
            long_description="Gamma works with banks",
            website="https://gamma.io",
            lastfunding="2024-04-01",
        )
        create_company(
            "Delta",
            ["Robotics"],
            5,
            founders=["Delta Founder"],
            description="Robotics automation platform",
            long_description="Warehouse robotics",
            website="https://delta-bots.example.com",
            lastfunding="2023-12-01",
        )

    def test_crunchbase_doc_to_company_shape_falls_back_to_total_fields(self):
        normalized = CompaniesListView._crunchbase_doc_to_company_shape(
            {
                "name": "MergedCo",
                "funding_total": "$42M",
                "funding_total_usd": 42.0,
            }
        )

        assert normalized["funding"] == "$42M"
        assert normalized["funding_usd"] == 42.0
        assert normalized["funding_total"] == "$42M"
        assert normalized["funding_total_usd"] == 42.0
        assert normalized["sources"] == ["crunchbase"]
        assert normalized["match_confidence"] == 1.0

    def test_build_root_query_supports_filter_families(self):
        filters = json.dumps(
            [
                {"id": "name", "value": "Alpha"},
                {"id": "description", "value": "vision"},
                {"id": "industries", "value": ["AI"], "operator": "any"},
                {
                    "id": "industry_groups",
                    "groups": [{"operator": "any", "industries": ["Fintech"]}],
                    "operator": "all",
                },
                {"id": "excluded_industries", "value": ["Robotics"]},
                {"id": "lastfunding", "value": "2024"},
                {"id": "website", "value": "example.com"},
                {
                    "id": "crunchbase_url",
                    "value": "https://crunchbase.com/organization/alpha",
                },
                {"id": "funding_usd", "value": [10, 30]},
                {"id": "funding", "value": "$2"},
            ]
        )

        query = CompaniesListView.build_root_query(filters=filters)
        clauses = query["$and"]

        assert {"name": {"$regex": "Alpha", "$options": "i"}} in clauses
        assert {"description": {"$regex": "vision", "$options": "i"}} in clauses
        assert {"$or": [{"industries": {"$regex": "^AI$", "$options": "i"}}]} in clauses
        assert {"$nor": [{"industries": {"$regex": "^Robotics$", "$options": "i"}}]} in clauses
        assert {"lastfunding": {"$regex": "2024", "$options": "i"}} in clauses
        assert {"website": {"$regex": "example.com", "$options": "i"}} in clauses
        assert {"crunchbase_url": "https://crunchbase.com/organization/alpha"} in clauses
        assert {
            "$or": [
                {"funding_usd": {"$gte": 10}},
                {"funding_total_usd": {"$gte": 10}},
            ]
        } in clauses
        assert {
            "$or": [
                {"funding_usd": {"$lte": 30}},
                {"funding_total_usd": {"$lte": 30}},
            ]
        } in clauses
        assert {
            "$or": [
                {"funding": {"$regex": "$2", "$options": "i"}},
                {"funding_total": {"$regex": "$2", "$options": "i"}},
            ]
        } in clauses

    def test_build_root_query_uses_search_over_filters(self):
        query = CompaniesListView.build_root_query(
            filters=json.dumps([{"id": "name", "value": "ShouldNotApply"}]),
            globalFilter="gamma.io",
        )

        assert "$or" in query
        assert query["$or"][0] == {"name": {"$regex": "gamma.io", "$options": "i"}}
        assert CompaniesListView.build_sort(
            sorting=[{"id": "funding", "desc": True}, {"id": "name"}]
        ) == [("funding_usd", -1), ("name", 1)]

    def test_list_returns_paginated_results_with_normalized_fields(self):
        request = self.factory.get(
            "/public/comp",
            {"sorting": json.dumps([{"id": "name", "desc": False}])},
        )
        response = CompaniesListView.as_view()(request)

        assert response.status_code == 200
        assert response.data["count"] == 4
        assert response.data["next"] is None
        assert response.data["previous"] is None
        assert company_names(response) == ["Alpha", "Beta", "Delta", "Gamma"]

        alpha = response.data["results"][0]
        assert alpha["funding"] == "$10"
        assert alpha["funding_usd"] == 10
        assert alpha["lastfunding"] == "2024-03-01"
        assert "last_funding_date" not in alpha
        assert "last_funding_type" not in alpha

    def test_list_applies_search_and_funding_sort_alias(self):
        search_request = self.factory.get("/public/comp", {"search": "gamma.io"})
        search_response = CompaniesListView.as_view()(search_request)

        assert search_response.status_code == 200
        assert company_names(search_response) == ["Gamma"]

        sort_request = self.factory.get(
            "/public/comp",
            {"sorting": json.dumps([{"id": "funding", "desc": True}])},
        )
        sort_response = CompaniesListView.as_view()(sort_request)

        assert sort_response.status_code == 200
        assert company_names(sort_response) == ["Beta", "Gamma", "Alpha", "Delta"]

    def test_list_applies_compound_filters_with_real_queries(self):
        filters = json.dumps(
            [
                {
                    "id": "industry_groups",
                    "groups": [
                        {"operator": "any", "industries": ["AI"]},
                        {"operator": "any", "industries": ["Fintech"]},
                    ],
                    "operator": "all",
                },
                {"id": "excluded_industries", "value": ["Robotics"]},
                {"id": "funding_usd", "value": [15, 25]},
                {"id": "website", "value": "gamma.io"},
                {"id": "funding", "value": "20"},
                {"id": "lastfunding", "value": "2024-04"},
                {
                    "id": "crunchbase_url",
                    "value": "https://crunchbase.com/organization/gamma",
                },
            ]
        )
        request = self.factory.get(
            "/public/comp",
            {
                "filters": filters,
                "sorting": json.dumps([{"id": "name", "desc": False}]),
            },
        )
        response = CompaniesListView.as_view()(request)

        assert response.status_code == 200
        assert company_names(response) == ["Gamma"]

    def test_list_applies_aggregate_funding_filter(self):
        request = self.factory.get(
            "/public/comp",
            {
                "filters": json.dumps(
                    [{"id": "aggregate_funding_usd", "value": [25, 35]}]
                ),
                "sorting": json.dumps([{"id": "name", "desc": False}]),
            },
        )
        response = CompaniesListView.as_view()(request)

        assert response.status_code == 200
        assert company_names(response) == ["Alpha", "Gamma"]

    def test_list_ignores_invalid_numeric_filters(self):
        request = self.factory.get(
            "/public/comp",
            {
                "filters": json.dumps(
                    [
                        {"id": "funding_usd", "value": ["bad", ""]},
                        {"id": "aggregate_funding_usd", "value": ["bad", None]},
                    ]
                ),
                "sorting": json.dumps([{"id": "name", "desc": False}]),
            },
        )
        response = CompaniesListView.as_view()(request)

        assert response.status_code == 200
        assert company_names(response) == ["Alpha", "Beta", "Delta", "Gamma"]

    def test_list_returns_empty_for_unmatched_aggregate_funding_filter(self):
        request = self.factory.get(
            "/public/comp",
            {
                "filters": json.dumps(
                    [{"id": "aggregate_funding_usd", "value": [999, 1000]}]
                ),
            },
        )
        response = CompaniesListView.as_view()(request)

        assert response.status_code == 200
        assert response.data["count"] == 0
        assert response.data["results"] == []


@pytest.mark.django_db
class TestSettingsList:
    def setup_method(self):
        self.factory = APIRequestFactory()

    def test_get_creates_default_interested_industries_and_flattens_mixed_values(self):
        create_company("Alpha", ["AI", "Fintech"], 10)
        beta = create_company("Beta", ["Robotics"], 20)
        raw_update_company(beta, industries="Robotics")

        assert InterestedIndustries.objects.filter(key="industry").count() == 0

        response = SettingsList.as_view()(self.factory.get("/public/settings"))

        assert response.status_code == 200
        assert response.data["industries"] == ["AI", "Fintech", "Robotics"]
        assert response.data["interested_industries"] == []
        assert InterestedIndustries.objects.filter(key="industry").count() == 1

    def test_get_excludes_existing_interested_industries(self):
        create_company("Alpha", ["AI", "Fintech"], 10)
        create_company("Beta", ["Robotics"], 20)
        InterestedIndustries.objects.create(key="industry", industries=["Fintech"])

        response = SettingsList.as_view()(self.factory.get("/public/settings"))

        assert response.status_code == 200
        assert response.data["industries"] == ["AI", "Robotics"]
        assert response.data["interested_industries"] == ["Fintech"]

    def test_post_creates_and_updates_interested_industries(self):
        create_request = self.factory.post(
            "/public/settings",
            {"industry": ["AI"]},
            format="json",
        )
        create_response = SettingsList.as_view()(create_request)

        assert create_response.status_code == 200
        assert create_response.data == "success"
        row = InterestedIndustries.objects.get(key="industry")
        assert row.industries == ["AI"]

        update_request = self.factory.post(
            "/public/settings",
            {"industry": ["Fintech", "Robotics"]},
            format="json",
        )
        update_response = SettingsList.as_view()(update_request)

        assert update_response.status_code == 200
        row.refresh_from_db()
        assert row.industries == ["Fintech", "Robotics"]


@pytest.mark.django_db
class TestIndustryFundingAnalytics:
    def setup_method(self):
        self.factory = APIRequestFactory()
        create_company("Alpha", ["AI"], 10)
        create_company("Beta", ["AI"], 30)
        create_company("Gamma", ["AI", "Fintech"], 20)
        create_company("Delta", ["Fintech"], 5)
        create_company("Epsilon", ["Ignored"], 0)

    def test_returns_median_for_even_and_odd_industry_groups(self):
        results = IndustryFundingAnalyticsView.get_queryset()
        result_map = {row["industry"]: row for row in results}

        assert result_map["AI"]["median_funding_usd"] == 20
        assert result_map["AI"]["company_count"] == 3
        assert result_map["Fintech"]["median_funding_usd"] == 12.5
        assert result_map["Fintech"]["company_count"] == 2

    def test_excludes_non_positive_funding(self):
        results = IndustryFundingAnalyticsView.get_queryset()
        industries = {row["industry"] for row in results}

        assert "Ignored" not in industries

    def test_filters_by_selected_industries(self):
        results = IndustryFundingAnalyticsView.get_queryset(
            industry_groups=[{"operator": "any", "industries": ["AI"]}],
        )

        assert {row["industry"] for row in results} == {"AI", "Fintech"}

    def test_supports_any_and_all_group_operators(self):
        any_results = IndustryFundingAnalyticsView.get_queryset(
            industry_groups=[
                {"operator": "any", "industries": ["AI"]},
                {"operator": "any", "industries": ["Fintech"]},
            ],
            industry_group_operator="any",
        )
        all_results = IndustryFundingAnalyticsView.get_queryset(
            industry_groups=[
                {"operator": "any", "industries": ["AI"]},
                {"operator": "any", "industries": ["Fintech"]},
            ],
            industry_group_operator="all",
        )

        any_map = {row["industry"]: row for row in any_results}
        all_map = {row["industry"]: row for row in all_results}

        assert any_map["AI"]["company_count"] == 3
        assert any_map["Fintech"]["company_count"] == 2
        assert all_map["AI"]["company_count"] == 1
        assert all_map["Fintech"]["company_count"] == 1

    def test_supports_or_inside_group_and_and_between_groups(self):
        results = IndustryFundingAnalyticsView.get_queryset(
            industry_groups=[
                {"operator": "any", "industries": ["AI", "Artificial Intelligence"]},
                {"operator": "any", "industries": ["Fintech", "Software"]},
            ],
            industry_group_operator="all",
        )

        result_map = {row["industry"]: row for row in results}

        assert result_map["AI"]["company_count"] == 1
        assert result_map["Fintech"]["company_count"] == 1

    def test_excludes_ignored_industries_from_analytics(self):
        results = IndustryFundingAnalyticsView.get_queryset(
            excluded_industries=["Fintech"],
        )

        result_map = {row["industry"]: row for row in results}

        assert "Fintech" not in result_map
        assert result_map["AI"]["company_count"] == 2

    def test_industry_total_mode_filters_on_aggregated_industry_funding(self):
        results = IndustryFundingAnalyticsView.get_queryset(
            funding_max=25,
            analytics_mode="industry_total",
        )

        result_map = {row["industry"]: row for row in results}

        assert "AI" not in result_map
        assert result_map["Fintech"]["total_funding_usd"] == 25
        assert result_map["Fintech"]["company_count"] == 2

    def test_list_response_shape_and_applied_filters(self):
        request = self.factory.get(
            "/public/analytics/industry-funding",
            {
                "search": "Gamma",
                "fundingMin": 15,
                "fundingMax": 25,
                "analyticsMode": "legacy",
                "industryGroupOperator": "all",
                "industryGroups": '[{"operator":"any","industries":["AI"]}]',
                "excludedIndustries": '["Software"]',
            },
        )
        response = IndustryFundingAnalyticsView.as_view()(request)

        assert response.status_code == 200
        assert response.data["metric"] == "median_funding_usd"
        assert response.data["applied_filters"] == {
            "search": "Gamma",
            "fundingMin": 15.0,
            "fundingMax": 25.0,
            "analyticsMode": "legacy",
            "industryGroupOperator": "all",
            "industryGroups": [{"operator": "any", "industries": ["AI"]}],
            "excludedIndustries": ["Software"],
        }
        assert response.data["results"] == [
            {
                "industry": "Fintech",
                "company_count": 1,
                "median_funding_usd": 20.0,
                "total_funding_usd": 20.0,
            },
            {
                "industry": "AI",
                "company_count": 1,
                "median_funding_usd": 20.0,
                "total_funding_usd": 20.0,
            },
        ]

    def test_list_falls_back_for_invalid_query_params(self):
        request = self.factory.get(
            "/public/analytics/industry-funding",
            {
                "analyticsMode": "invalid",
                "industryGroupOperator": "invalid",
                "industryGroups": "not-json",
                "excludedIndustries": "not-json",
            },
        )
        response = IndustryFundingAnalyticsView.as_view()(request)

        assert response.status_code == 200
        assert response.data["metric"] == "median_funding_usd"
        assert response.data["applied_filters"] == {
            "search": "",
            "fundingMin": None,
            "fundingMax": None,
            "analyticsMode": "legacy",
            "industryGroupOperator": "any",
            "industryGroups": [],
            "excludedIndustries": [],
        }
        assert {row["industry"] for row in response.data["results"]} == {"AI", "Fintech"}

    def test_list_supports_legacy_industries_array_fallback(self):
        request = self.factory.get(
            "/public/analytics/industry-funding",
            [
                ("industries[]", "AI"),
                ("industries[]", "Fintech"),
                ("industryMode", "all"),
            ],
        )
        response = IndustryFundingAnalyticsView.as_view()(request)

        assert response.status_code == 200
        assert response.data["applied_filters"]["industryGroups"] == [
            {"operator": "all", "industries": ["AI", "Fintech"]}
        ]
        assert {row["industry"] for row in response.data["results"]} == {"AI", "Fintech"}
        assert all(row["company_count"] == 1 for row in response.data["results"])

    def test_list_returns_industry_total_metric_with_bounds(self):
        request = self.factory.get(
            "/public/analytics/industry-funding",
            {
                "analyticsMode": "industry_total",
                "fundingMin": 26,
                "fundingMax": 60,
            },
        )
        response = IndustryFundingAnalyticsView.as_view()(request)

        assert response.status_code == 200
        assert response.data["metric"] == "total_funding_usd"
        assert response.data["results"] == [
            {
                "industry": "AI",
                "company_count": 3,
                "median_funding_usd": 20.0,
                "total_funding_usd": 60.0,
            }
        ]

    def test_returns_all_matching_industries_for_chart(self):
        Crunchbase.objects.all().delete()
        for index in range(105):
            create_company(f"Company{index}", [f"Industry {index}"], index + 1)

        results = IndustryFundingAnalyticsView.get_queryset()

        assert len(results) == 105
        assert results[0]["industry"] == "Industry 104"
        assert results[-1]["industry"] == "Industry 0"


@pytest.mark.django_db
class TestIndustryOverviewAnalytics:
    def setup_method(self):
        self.factory = APIRequestFactory()
        create_company("Alpha", ["AI", "Software"], 10)
        create_company("Beta", ["AI"], 30)
        create_company("Gamma", ["Fintech"], 20)
        create_company("Delta", ["Software"], 0)

    def test_returns_summary_and_both_distributions(self):
        request = self.factory.get("/public/analytics/industry-overview", {"topN": 10})
        response = IndustryOverviewAnalyticsView.as_view()(request)

        assert response.status_code == 200
        assert response.data["topN"] == 10
        assert response.data["summary"] == {
            "total_companies": 4,
            "funded_companies": 3,
            "total_funding_usd": 60.0,
            "total_industries": 3,
        }

        company_map = {
            row["industry"]: row["company_count"]
            for row in response.data["industry_by_company_count"]
        }
        assert company_map == {
            "AI": 2,
            "Software": 2,
            "Fintech": 1,
        }

        funding_map = {
            row["industry"]: row["total_funding_usd"]
            for row in response.data["industry_by_total_funding"]
        }
        assert funding_map == {
            "AI": 40.0,
            "Fintech": 20.0,
            "Software": 10.0,
        }

    def test_defaults_invalid_and_clamped_top_n_values(self):
        default_response = IndustryOverviewAnalyticsView.as_view()(
            self.factory.get("/public/analytics/industry-overview")
        )
        invalid_response = IndustryOverviewAnalyticsView.as_view()(
            self.factory.get("/public/analytics/industry-overview", {"topN": "oops"})
        )
        low_response = IndustryOverviewAnalyticsView.as_view()(
            self.factory.get("/public/analytics/industry-overview", {"topN": 1})
        )
        high_response = IndustryOverviewAnalyticsView.as_view()(
            self.factory.get("/public/analytics/industry-overview", {"topN": 999})
        )

        assert default_response.data["topN"] == 50
        assert invalid_response.data["topN"] == 50
        assert low_response.data["topN"] == 5
        assert high_response.data["topN"] == 200


@pytest.mark.django_db
class TestIndustryOverviewAnalyticsEmptyDataset:
    def test_returns_empty_summary_for_empty_dataset(self):
        factory = APIRequestFactory()

        response = IndustryOverviewAnalyticsView.as_view()(
            factory.get("/public/analytics/industry-overview")
        )

        assert response.status_code == 200
        assert response.data == {
            "summary": {
                "total_companies": 0,
                "funded_companies": 0,
                "total_funding_usd": 0.0,
                "total_industries": 0,
            },
            "topN": 50,
            "industry_by_company_count": [],
            "industry_by_total_funding": [],
        }


@pytest.mark.django_db
class TestFundingBracketDistributionAnalytics:
    def setup_method(self):
        self.factory = APIRequestFactory()
        create_company("PreSeed", ["AI", "Software"], 500_000)
        create_company("Seed", ["AI"], 2_000_000)
        create_company("SeriesA", ["Fintech"], 8_000_000)
        create_company("SeriesC", ["Fintech", "Enterprise"], 30_000_000)
        create_company("LateStage", ["Enterprise"], 150_000_000)
        create_company("NoFunding", ["AI"], 0)
        create_company("NoIndustry", [], 4_000_000)

    def test_helper_edges_cover_invalid_and_large_values(self):
        assert FundingBracketDistributionView._coerce_funding("oops") is None
        assert FundingBracketDistributionView._coerce_funding(0) is None
        assert get_funding_bracket_meta(-1) is None
        assert get_funding_bracket_meta(600_000)["key"] == "600k_to_850k"
        assert get_funding_bracket_meta(6_000_000_000)["key"] == "5b_plus"

    def test_returns_all_brackets_with_full_breakdown(self):
        request = self.factory.get("/public/analytics/funding-bracket-distribution")
        response = FundingBracketDistributionView.as_view()(request)

        assert response.status_code == 200
        assert response.data["summary"] == {
            "total_companies": 7,
            "funded_companies": 6,
            "bracketed_companies": 5,
            "excluded_without_funding": 1,
            "excluded_without_industries": 1,
            "total_funding_usd": 194500000.0,
            "coverage_ratio": pytest.approx(5 / 6),
        }

        bracket_map = {row["key"]: row for row in response.data["brackets"]}

        assert len(bracket_map) == len(FUNDING_BRACKETS)

        assert bracket_map["400k_to_600k"]["company_count"] == 1
        assert bracket_map["400k_to_600k"]["median_funding_usd"] == 500000.0
        assert bracket_map["400k_to_600k"]["industries"] == [
            {
                "industry": "Software",
                "company_count": 1,
                "total_funding_usd": 500000.0,
            },
            {
                "industry": "AI",
                "company_count": 1,
                "total_funding_usd": 500000.0,
            },
        ]

        assert bracket_map["2m_to_3m"]["company_count"] == 1
        assert bracket_map["2m_to_3m"]["total_funding_usd"] == 2000000.0
        assert bracket_map["7_5m_to_10m"]["company_count"] == 1
        assert bracket_map["25m_to_35m"]["company_count"] == 1
        assert bracket_map["150m_to_250m"]["company_count"] == 1

        assert bracket_map["25m_to_35m"]["industries"] == [
            {
                "industry": "Fintech",
                "company_count": 1,
                "total_funding_usd": 30000000.0,
            },
            {
                "industry": "Enterprise",
                "company_count": 1,
                "total_funding_usd": 30000000.0,
            },
        ]


@pytest.mark.django_db
class TestFundingBracketDistributionAnalyticsEdgeCases:
    def setup_method(self):
        self.factory = APIRequestFactory()

    def test_deduplicates_whitespace_industries_in_payload(self):
        create_company("CleanMe", [" AI ", "AI", " Fintech ", ""], 600_000)

        response = FundingBracketDistributionView.as_view()(
            self.factory.get("/public/analytics/funding-bracket-distribution")
        )

        assert response.status_code == 200
        bracket = next(
            row for row in response.data["brackets"] if row["key"] == "600k_to_850k"
        )
        industry_map = {
            row["industry"]: row["company_count"] for row in bracket["industries"]
        }

        assert bracket["company_count"] == 1
        assert industry_map == {"Fintech": 1, "AI": 1}

    def test_returns_zero_coverage_when_no_companies_are_funded(self):
        create_company("Dormant", ["AI"], 0)
        create_company("Inactive", ["Fintech"], 0)

        response = FundingBracketDistributionView.as_view()(
            self.factory.get("/public/analytics/funding-bracket-distribution")
        )

        assert response.status_code == 200
        assert response.data["summary"] == {
            "total_companies": 2,
            "funded_companies": 0,
            "bracketed_companies": 0,
            "excluded_without_funding": 2,
            "excluded_without_industries": 0,
            "total_funding_usd": 0.0,
            "coverage_ratio": 0.0,
        }
        assert all(row["company_count"] == 0 for row in response.data["brackets"])
