from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from rest_framework import serializers

from .models import JobAdvert, JobApplication, User


class CreateUserSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(min_length=4)

    def validate(self, attrs: dict):
        email: str = attrs.get("email")
        cleaned_email = email.lower().strip()
        if get_user_model().objects.filter(email__iexact=cleaned_email).exists():
            raise serializers.ValidationError({"email": "Email already exists."})
        attrs["email"] = cleaned_email
        return super().validate(attrs)

    def create(self, validated_data: dict):
        data = {
            "email": validated_data.get("email"),
            "password": make_password(validated_data.get("password")),
        }
        user: User = User.objects.create(**data)
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(allow_blank=False)


class JobApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobApplication
        fields = [
            "first_name",
            "last_name",
            "email",
            "phone",
            "linkedin_url",
            "github_url",
            "website",
            "experience_years",
            "cover_letter",
            "job_advert",
        ]

        extra_kwargs = {
            "job_advert": {"read_only": True},
        }

    def create(self, validated_data):
        job_advert: JobAdvert = self.context["job_advert"]
        validated_data["job_advert"] = job_advert
        return super().create(validated_data)


class CreateJobAdvertSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobAdvert
        fields = [
            "id",
            "title",
            "company_name",
            "employment_type",
            "experience_level",
            "description",
            "location",
            "is_published",
            "created_at",
        ]

        extra_kwargs = {
            "created_at": {"read_only": True},
        }


class ListJobAdvertSerializer(serializers.ModelSerializer):
    applicant_count = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = JobAdvert
        fields = [
            "id",
            "title",
            "company_name",
            "employment_type",
            "experience_level",
            "description",
            "location",
            "is_published",
            "created_at",
            "applicant_count",
        ]

    def get_applicant_count(self, obj: JobAdvert) -> int:
        return obj.applications.count()


class JobAdvertScheduleSerializer(serializers.Serializer):
    date_time = serializers.DateTimeField()
