from rest_framework import serializers
from .models import Crunchbase
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
