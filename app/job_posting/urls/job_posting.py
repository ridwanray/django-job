from django.urls import include, path
from rest_framework.routers import DefaultRouter

from ..views import JobViewSet

app_name = "job_posting"

router = DefaultRouter()
router.register("", JobViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
