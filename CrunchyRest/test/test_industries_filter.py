from databucket.models import Crunchbase
from public.views import IndustryList
from rest_framework.test import APIRequestFactory
import unittest
import pytest


@pytest.mark.django_db  # This mark allows access to the database
class TestIndustryFilter(unittest.TestCase):

    def setUp(self):
        Crunchbase.objects.create(name="Company1",
                                  website="https://test.com",
                                  logo="https://logo.com",
                                  founders=["Founder1", "Founder2"],
                                  similar_companies=["Company2", "Company3"],
                                  description="Test Description",
                                  long_description="Long Description",
                                  industries=[
                                      "Artificial Intelligence", "Tech"],
                                  founded="2020-01-01",
                                  lastfunding="2020-01-01")

        Crunchbase.objects.create(name="Company2",
                                  website="https://test.com",
                                  logo="https://logo.com",
                                  founders=["Founder1", "Founder2"],
                                  similar_companies=["Company2", "Company3"],
                                  description="Test Description",
                                  long_description="Long Description",
                                  industries=[
                                      "Artificial Intelligence", "Finance"],
                                  founded="2020-01-01",
                                  lastfunding="2020-01-01")

        Crunchbase.objects.create(name="Company3",
                                  website="https://test.com",
                                  logo="https://logo.com",
                                  founders=["Founder1", "Founder2"],
                                  similar_companies=["Company2", "Company3"],
                                  description="Test Description",
                                  long_description="Long Description",
                                  industries=["Finance"],
                                  founded="2020-01-01",
                                  lastfunding="2020-01-01")

        Crunchbase.objects.create(name="Company4",
                                  website="https://test.com",
                                  logo="https://logo.com",
                                  founders=["Founder1", "Founder2"],
                                  similar_companies=["Company2", "Company3"],
                                  description="Test Description",
                                  long_description="Long Description",
                                  industries=[
                                      "Artificial Intelligence"],
                                  founded="2020-01-01",
                                  lastfunding="2020-01-01")

    def test_get_queryset_with_selected(self):
        factory = APIRequestFactory()
        request = factory.get(
            '/industries', {'selected[]': ['Artificial Intelligence', 'Finance']})
        view = IndustryList.as_view()
        response = view(request)
        assert response.status_code == 200
        assert "Artificial Intelligence" in response.data
        assert "Finance" in response.data
        assert 2 == len(response.data)

    def test_get_queryset_with_selected(self):
        factory = APIRequestFactory()
        request = factory.get(
            '/industries', {'selected[]': ['Artificial Intelligence']})
        view = IndustryList.as_view()
        response = view(request)
        assert response.status_code == 200
        assert 3 == len(response.data)

    def test_get_queryset_with_selected_empty(self):
        factory = APIRequestFactory()
        request = factory.get(
            '/industries', {'selected[]': []})
        view = IndustryList.as_view()
        response = view(request)
        assert response.status_code == 200
        assert 3 == len(response.data)

    def test_get_queryset_with_selected_none(self):
        factory = APIRequestFactory()
        request = factory.get(
            '/industries')
        view = IndustryList.as_view()
        response = view(request)
        assert response.status_code == 200
        assert 3 == len(response.data)

    def test_get_queryset_with_selected_invalid(self):
        factory = APIRequestFactory()
        request = factory.get(
            '/industries', {'selected[]': ['Invalid']})
        view = IndustryList.as_view()
        response = view(request)
        assert response.status_code == 200
        assert 0 == len(response.data)

    def test_get_queryset_with_selected_invalid_and_valid(self):
        factory = APIRequestFactory()
        request = factory.get(
            '/industries', {'selected[]': ['Artificial Intelligence', 'Invalid']})
        view = IndustryList.as_view()
        response = view(request)
        assert response.status_code == 200
        assert 0 == len(response.data)


if __name__ == '__main__':
    unittest.main()
