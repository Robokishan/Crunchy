from rest_framework.decorators import api_view
from rest_framework.response import Response
from databucket.serializer import CrunchbaseSerializer
from databucket.models import Crunchbase
from bson import ObjectId
from django.db.models import Q


@api_view(['GET'])
def getCompanies(request):

    company_id = request.GET.get("id")

    if company_id:
        try:
            company_id = ObjectId(company_id)
            queryset = Crunchbase.objects.get(_id=company_id)
            serialized_data = CrunchbaseSerializer(
                queryset).data
            return Response(serialized_data)
        except Exception as e:
            print(e)
            return Response("Doesn't exist", status=404)
    else:
        page = request.GET.get("page", 1)
        page_size = request.GET.get("limit", 60)

        searchText = request.GET.get('search', None)

        if page < 1:
            page = 1

        if page_size > 500:
            page_size = 500

        queryset = Crunchbase.objects.all().order_by("-updated_at")
        if searchText:
            filters = {
                '$text': {
                    '$search': searchText,
                    '$language': 'en',  # Specify the language if needed
                    '$caseSensitive': False,  # Set to True for case-sensitive search
                    '$diacriticSensitive': False  # Set to True for diacritic-sensitive search
                }
            }
            queryset = queryset.filter(
                Q(industries__icontains=searchText) |
                Q(description__icontains=searchText) |
                Q(long_description__icontains=searchText) |
                Q(founders__icontains=searchText)
            )

        start_index = (page - 1) * page_size
        end_index = page * page_size

        # print(queryset)

        # serialized_data = CrunchbaseSerializer(
        #     queryset[start_index:end_index], many=True).data

        # all the company list without any limit
        serialized_data = CrunchbaseSerializer(
            queryset, many=True).data
        return Response(serialized_data)
