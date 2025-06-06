from rest_framework import serializers

from integrations.models import ContextualEvent, ContextualData


class ContextualEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContextualEvent
        fields = [
            'uid',
            'event_type',
            'event_date',
            'location',
            'city',
            'category',
            'extra_fields',
            'created_at',
        ]


class ContextualDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContextualData
        fields = [
            'uid',
            'event',
            'version',
            'fetched_at',
            'extra_fields',
        ]
        depth = 1
