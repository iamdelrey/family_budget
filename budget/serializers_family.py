from rest_framework import serializers
from .models import Family

class CreateFamilySerializer(serializers.ModelSerializer):
    class Meta:
        model = Family
        fields = ['name']

    def create(self, validated_data):
        user = self.context['request'].user
        return Family.objects.create(created_by=user, **validated_data)
