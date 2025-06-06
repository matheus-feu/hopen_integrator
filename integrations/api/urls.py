from django.urls import include
from django.urls import path

from integrations.api.routers import router

app_name = 'integrations'

urlpatterns = [
    path('', include(router.urls)),
]
