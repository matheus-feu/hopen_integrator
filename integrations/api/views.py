from drf_spectacular.utils import extend_schema
from rest_framework import viewsets
from rest_framework.permissions import DjangoModelPermissions, IsAdminUser

from integrations.api.serializers import ContextualEventSerializer, ContextualDataSerializer
from integrations.filters import ContextualEventFilterClass, ContextualDataFilterClass
from integrations.models import ContextualEvent, ContextualData


@extend_schema(tags=['integrations'])
class ContextualEventViewSet(viewsets.ModelViewSet):
    """
    API endpoint que permite visualizar ou editar eventos contextuais.
    Suporta filtros por localização, cidade, data, categoria e tipo de evento.
    """
    queryset = ContextualEvent.objects.select_related('event').all()
    serializer_class = ContextualEventSerializer
    rql_filter_class = ContextualEventFilterClass
    permission_classes = [DjangoModelPermissions, IsAdminUser]


@extend_schema(tags=['integrations'])
class ContextualDataViewSet(viewsets.ModelViewSet):
    """
    API endpoint que permite visualizar ou editar dados contextuais.
    Suporta filtros por evento, integração e versão.
    """
    queryset = ContextualData.objects.all()
    serializer_class = ContextualDataSerializer
    rql_filter_class = ContextualDataFilterClass
    permission_classes = [DjangoModelPermissions, IsAdminUser]
