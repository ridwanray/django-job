from django.urls import include, path
from rest_framework.routers import DefaultRouter

from ..views import AuthViewsets

app_name = "auth"

router = DefaultRouter()
router.register("", AuthViewsets, basename="auth")

urlpatterns = [
    path("", include(router.urls)),
]
