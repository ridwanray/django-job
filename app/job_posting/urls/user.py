from django.urls import include, path
from rest_framework.routers import DefaultRouter

from ..views import CreateUserViewSet

app_name = "user"
router = DefaultRouter()
router.register("", CreateUserViewSet, basename="user")

urlpatterns = [
    path("", include(router.urls)),
]
