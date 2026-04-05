import pytest
from rest_framework.test import APIRequestFactory

from databucket.models import Crunchbase
from public.views import IndustryList


def create_company(name, industries):
    Crunchbase.objects.create(
        name=name,
        funding="",
        funding_usd=0,
        rate=0,
        website=f"https://{name.lower()}.example.com",
        crunchbase_url=f"https://crunchbase.com/organization/{name.lower()}",
        logo="https://logo.example.com/logo.png",
        founders=["Founder1", "Founder2"],
        similar_companies=["Company2", "Company3"],
        description="Test Description",
        long_description="Long Description",
        acquired="",
        industries=industries,
        founded="2020-01-01",
        lastfunding="2020-01-01",
        stocksymbol="",
    )


def industry_names(response):
    return [row["industry"] for row in response.data]


@pytest.mark.django_db
class TestIndustryFilter:
    def setup_method(self):
        self.factory = APIRequestFactory()
        create_company("Company1", ["Artificial Intelligence", "Tech"])
        create_company("Company2", ["Artificial Intelligence", "Finance"])
        create_company("Company3", ["Finance"])
        create_company("Company4", ["Artificial Intelligence"])

    def test_returns_matching_industries_for_multiple_selected(self):
        request = self.factory.get(
            "/industries",
            {"selected[]": ["Artificial Intelligence", "Finance"]},
        )
        response = IndustryList.as_view()(request)
        result_map = {row["industry"]: row["count"] for row in response.data}

        assert response.status_code == 200
        assert result_map == {
            "Artificial Intelligence": 1,
            "Finance": 1,
        }

    def test_returns_all_matching_industries_for_single_selected(self):
        request = self.factory.get(
            "/industries",
            {"selected[]": ["Artificial Intelligence"]},
        )
        response = IndustryList.as_view()(request)
        result_map = {row["industry"]: row["count"] for row in response.data}

        assert response.status_code == 200
        assert result_map == {
            "Artificial Intelligence": 3,
            "Finance": 1,
            "Tech": 1,
        }

    def test_returns_default_industry_order_without_selection(self):
        response = IndustryList.as_view()(self.factory.get("/industries"))

        assert response.status_code == 200
        assert industry_names(response) == [
            "Artificial Intelligence",
            "Finance",
            "Tech",
        ]

    def test_returns_same_default_order_for_empty_selection(self):
        response = IndustryList.as_view()(
            self.factory.get("/industries", {"selected[]": []})
        )

        assert response.status_code == 200
        assert industry_names(response) == [
            "Artificial Intelligence",
            "Finance",
            "Tech",
        ]

    def test_returns_empty_for_invalid_selected_industry(self):
        response = IndustryList.as_view()(
            self.factory.get("/industries", {"selected[]": ["Invalid"]})
        )

        assert response.status_code == 200
        assert response.data == []

    def test_returns_empty_for_invalid_and_valid_selected_mix(self):
        response = IndustryList.as_view()(
            self.factory.get(
                "/industries",
                {"selected[]": ["Artificial Intelligence", "Invalid"]},
            )
        )

        assert response.status_code == 200
        assert response.data == []

    def test_ignores_blank_selected_values(self):
        response = IndustryList.as_view()(
            self.factory.get(
                "/industries",
                [("selected[]", ""), ("selected[]", "Artificial Intelligence")],
            )
        )
        result_map = {row["industry"]: row["count"] for row in response.data}

        assert response.status_code == 200
        assert result_map == {
            "Artificial Intelligence": 3,
            "Finance": 1,
            "Tech": 1,
        }

    def test_supports_alphabetical_sort_for_selected_results(self):
        response = IndustryList.as_view()(
            self.factory.get(
                "/industries",
                {"selected[]": ["Artificial Intelligence"], "sortBy": "alphabetical"},
            )
        )

        assert response.status_code == 200
        assert industry_names(response) == [
            "Artificial Intelligence",
            "Finance",
            "Tech",
        ]

    def test_supports_industry_count_sort_for_selected_results(self):
        response = IndustryList.as_view()(
            self.factory.get(
                "/industries",
                {"selected[]": ["Artificial Intelligence"], "sortBy": "industryCount"},
            )
        )

        assert response.status_code == 200
        assert response.data[0] == {"industry": "Artificial Intelligence", "count": 3}
        assert [row["count"] for row in response.data] == [3, 1, 1]
