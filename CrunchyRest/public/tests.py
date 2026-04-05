import pytest
from rest_framework.test import APIRequestFactory

from databucket.models import Crunchbase
from public.views import (
    FundingBracketDistributionView,
    IndustryFundingAnalyticsView,
    IndustryOverviewAnalyticsView,
)


def create_company(name, industries, funding_usd, created_at=None):
    payload = {
        "name": name,
        "funding": f"${funding_usd}" if funding_usd else "",
        "funding_usd": funding_usd,
        "rate": 0,
        "website": f"https://{name.lower()}.example.com",
        "crunchbase_url": f"https://crunchbase.com/organization/{name.lower()}",
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
    company = Crunchbase.objects.create(**payload)
    if created_at is not None:
        company.created_at = created_at
        company.save()
    return company


@pytest.mark.django_db
class TestIndustryFundingAnalytics:
    def setup_method(self):
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
        factory = APIRequestFactory()
        request = factory.get(
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
            },
            {
                "industry": "AI",
                "company_count": 1,
                "median_funding_usd": 20.0,
            },
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
        create_company("Alpha", ["AI", "Software"], 10)
        create_company("Beta", ["AI"], 30)
        create_company("Gamma", ["Fintech"], 20)
        create_company("Delta", ["Software"], 0)

    def test_returns_summary_and_both_distributions(self):
        factory = APIRequestFactory()
        request = factory.get("/public/analytics/industry-overview", {"topN": 10})
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


@pytest.mark.django_db
class TestFundingBracketDistributionAnalytics:
    def setup_method(self):
        create_company("PreSeed", ["AI", "Software"], 500_000)
        create_company("Seed", ["AI"], 2_000_000)
        create_company("SeriesA", ["Fintech"], 8_000_000)
        create_company("SeriesC", ["Fintech", "Enterprise"], 30_000_000)
        create_company("LateStage", ["Enterprise"], 150_000_000)
        create_company("NoFunding", ["AI"], 0)
        create_company("NoIndustry", [], 4_000_000)

    def test_returns_all_brackets_with_full_breakdown(self):
        factory = APIRequestFactory()
        request = factory.get("/public/analytics/funding-bracket-distribution")
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

        assert len(bracket_map) == 30

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
