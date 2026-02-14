from rest_framework import serializers
from .models import Crunchbase, Company
import json


class ListField(serializers.Field):
    def to_representation(self, value):
        return value

    def to_internal_value(self, data):
        if isinstance(data, list):
            return data
        elif isinstance(data, str):
            try:
                return json.loads(data)
            except ValueError:
                return []
                # raise serializers.ValidationError("Invalid JSON string.")
        else:
            return []
            # raise serializers.ValidationError(
            #     "Invalid data type. Expecting a list or JSON string.")


class CrunchbaseSerializer(serializers.ModelSerializer):
    founders = ListField()
    similar_companies = ListField()
    industries = ListField()

    class Meta:
        model = Crunchbase
        fields = '__all__'


class CompanySerializer(serializers.ModelSerializer):
    """Serializer for the unified Company model."""
    founders = ListField()
    similar_companies = ListField()
    industries = ListField()
    funding = serializers.CharField(read_only=True, allow_blank=True, allow_null=True)
    funding_usd = serializers.FloatField(read_only=True, allow_null=True)
    lastfunding = serializers.CharField(read_only=True, allow_blank=True, allow_null=True)
    funding_rounds = ListField()
    sources = ListField()
    source_priority = serializers.JSONField()
    _id = serializers.CharField(read_only=True)

    class Meta:
        model = Company
        fields = '__all__'
