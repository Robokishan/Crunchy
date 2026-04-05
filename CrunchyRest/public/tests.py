import pytest
from rest_framework.test import APIRequestFactory

from databucket.models import Crunchbase
from public.views import IndustryFundingAnalyticsView


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

    def test_list_response_shape_and_applied_filters(self):
        factory = APIRequestFactory()
        request = factory.get(
            "/public/analytics/industry-funding",
            {
                "search": "Gamma",
                "fundingMin": 15,
                "fundingMax": 25,
                "industryGroupOperator": "all",
                "industryGroups": '[{"operator":"any","industries":["AI"]}]',
            },
        )
        response = IndustryFundingAnalyticsView.as_view()(request)

        assert response.status_code == 200
        assert response.data["metric"] == "median_funding_usd"
        assert response.data["applied_filters"] == {
            "search": "Gamma",
            "fundingMin": 15.0,
            "fundingMax": 25.0,
            "industryGroupOperator": "all",
            "industryGroups": [{"operator": "any", "industries": ["AI"]}],
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

    def test_caps_results_at_100_industries(self):
        Crunchbase.objects.all().delete()
        for index in range(105):
            create_company(f"Company{index}", [f"Industry {index}"], index + 1)

        results = IndustryFundingAnalyticsView.get_queryset()

        assert len(results) == 100
        assert results[0]["industry"] == "Industry 104"
        assert results[-1]["industry"] == "Industry 5"
