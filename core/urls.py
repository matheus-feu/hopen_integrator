from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView
)


urlpatterns = [
      path('admin/', admin.site.urls),
      path('i18n/', include('django.conf.urls.i18n')),

      # API URLs
      path('api/v1/integrations/', include('integrations.api.urls', namespace='integrations')),

      # Authentication URLs
      path('api/v1/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
      path('api/v1/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
      path('api/v1/token/verify/', TokenVerifyView.as_view(), name='token_verify'),

      # API Documentation
      path('api/v1/schema/', SpectacularAPIView.as_view(), name='schema'),
      path('api/v1/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
      path('api/v1/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
