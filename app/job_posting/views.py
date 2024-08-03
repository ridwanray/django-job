from django.contrib.auth import authenticate
from django.db.models import Count
from drf_spectacular.utils import extend_schema
from rest_framework import status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from .models import JobAdvert
from .serializers import (
    CreateJobAdvertSerializer,
    CreateUserSerializer,
    JobAdvertScheduleSerializer,
    JobApplicationSerializer,
    ListJobAdvertSerializer,
    LoginSerializer,
)
from .tasks import schedule_job_advert


class CreateUserViewSet(viewsets.GenericViewSet):
    """Enables a user to sign up"""

    serializer_class = CreateUserSerializer
    permission_classes = [AllowAny]

    @extend_schema(
        responses={
            200: {
                "type": "object",
                "properties": {
                    "message": {"type": "string", "example": "Account created"},
                },
            }
        },
    )
    def create(self, request: Request, *args, **kwargs):
        context = {"request": request}
        serializer = CreateUserSerializer(data=request.data, context=context)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"message": "Account created!"}, status.HTTP_200_OK)


class AuthViewsets(viewsets.GenericViewSet):
    """Auth viewsets"""

    serializer_class = LoginSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={
            200: {
                "type": "object",
                "properties": {
                    "token": {"type": "string", "example": "xyz"},
                },
            }
        },
    )
    @action(
        methods=["POST"],
        detail=False,
        serializer_class=LoginSerializer,
        url_path="login",
        permission_classes=[AllowAny],
    )
    def login(self, request: Request, pk=None):
        """Login with email and password"""
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = authenticate(
            email=serializer.data["email"], password=serializer.data["password"]
        )
        if not user:
            return Response({"error": "Invalid credentials"}, 400)
        token, _ = Token.objects.get_or_create(user=user)
        return Response({"token": token.key}, status=200)

    @extend_schema(request=None, responses=None)
    @action(
        methods=["POST"],
        detail=False,
        url_path="logout",
        permission_classes=[IsAuthenticated],
    )
    def logout(self, request: Request):
        request.user.auth_token.delete()
        return Response({"message": "Logged out"}, status=status.HTTP_200_OK)


class JobViewSet(viewsets.ModelViewSet):
    queryset = JobAdvert.objects.all()
    serializer_class = ListJobAdvertSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "post", "patch","delete"]

    def get_queryset(self):
        queryset = JobAdvert.objects.annotate(
            application_count=Count("applications")
        ).order_by("-is_published", "-application_count", "-created_at")

        if not self.request.user.is_authenticated:
            queryset = queryset.filter(is_published=True)

        return queryset

    def get_permissions(self):
        permission_classes = self.permission_classes
        if self.action in ["apply", "list", "retrieve"]:
            permission_classes = [AllowAny]
        return [permission() for permission in permission_classes]

    def get_serializer_class(self):
        if self.action in ["create"]:
            return CreateJobAdvertSerializer
        return super().get_serializer_class()

    def paginate_results(self, queryset):
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @extend_schema(
        request=None,
        responses={
            200: {
                "type": "object",
                "properties": {
                    "message": {"type": "string", "example": "Advert published."},
                },
            },
        },
    )
    @action(
        methods=["POST"],
        detail=True,
    )
    def publish(self, request: Request, pk=None):
        """Set a job advert as published"""
        job_advert: JobAdvert = self.get_object()
        job_advert.is_published = True
        job_advert.save(update_fields=["is_published"])
        return Response({"message": "Advert published."})

    @extend_schema(
        request=None,
        responses={
            200: {
                "type": "object",
                "properties": {
                    "message": {"type": "string", "example": "Advert unpublished."},
                },
            },
        },
    )
    @action(methods=["POST"], detail=True)
    def unpublish(self, request: Request, pk=None):
        job_advert: JobAdvert = self.get_object()
        job_advert.is_published = False
        job_advert.save(update_fields=["is_published"])
        return Response({"message": "Advert unpublished."})

    def destroy(self, request: Request, *args, **kwargs):
        job_advert: JobAdvert = self.get_object()
        if job_advert.is_published:
            return Response({"error": "Only unpublished adverts can be deleted."}, 400)
        return super().destroy(request, *args, **kwargs)

    @action(
        methods=["POST"],
        detail=True,
        url_path="apply",
        serializer_class=JobApplicationSerializer,
    )
    def apply(self, request: Request, pk=None):
        """Apply for this job advert"""
        job_advert: JobAdvert = self.get_object()
        if not job_advert.is_published:
            return Response({"error": "You can only apply for published advert"}, 400)

        serializer = JobApplicationSerializer(
            data=request.data, context={"job_advert": job_advert}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"message": "Applied Successfully."})

    @extend_schema(responses=JobApplicationSerializer(many=True))
    @action(
        methods=["GET"],
        detail=True,
        url_path="applications",
        serializer_class=JobApplicationSerializer,
    )
    def applications(self, request: Request, pk=None):
        """Returns the job applications that belongs to a job advert"""
        job_advert: JobAdvert = self.get_object()
        job_applications = job_advert.applications.all()
        return self.paginate_results(job_applications)

    @action(
        methods=["POST"],
        detail=True,
        url_path="schedule",
        serializer_class=JobAdvertScheduleSerializer,
    )
    def schedule_advert(self, request: Request, pk=None):
        """Schedule when an advert is expected to be published"""
        job_advert: JobAdvert = self.get_object()
        if job_advert.is_published:
            return Response(
                {"error": "You can only schedule an unpublished advert."}, 400
            )

        serializer = JobAdvertScheduleSerializer(
            data=request.data, context={"job_advert": job_advert}
        )
        serializer.is_valid(raise_exception=True)
        schedule_job_advert.apply_async(
            kwargs={"job_id": job_advert.id}, eta=serializer.data["date_time"]
        )
        return Response({"message": "Scheduled successfully."})
