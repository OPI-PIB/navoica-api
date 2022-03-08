from rest_framework import serializers
from navoica_api.models import CareerModel


class CareerSerializer(serializers.ModelSerializer):
    class Meta:
        model = CareerModel
        fields = '__all__'
        lookup_field = 'id'
