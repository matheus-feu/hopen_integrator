from rest_framework.routers import DefaultRouter

from integrations.api.views import ContextualEventViewSet, ContextualDataViewSet

router = DefaultRouter()
router.register(r'contextual-events', ContextualEventViewSet, basename='contextual-events')
router.register(r'contextual-data', ContextualDataViewSet, basename='contextual-data')
