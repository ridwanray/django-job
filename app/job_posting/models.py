from common.models import AuditableModel
from django.contrib.auth.models import AbstractBaseUser
from django.db import models

from .enums import EmploymentType, ExperienceLevel, YearOfExperience
from .managers import CustomUserManager


class User(AbstractBaseUser, AuditableModel):
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []
    objects = CustomUserManager()

    class Meta:
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return self.email


class JobAdvert(AuditableModel):
    title = models.CharField(max_length=150)
    company_name = models.CharField(max_length=150)
    employment_type = models.CharField(max_length=50, choices=EmploymentType)
    experience_level = models.CharField(max_length=50, choices=ExperienceLevel)
    description = models.TextField()
    location = models.CharField(max_length=200)
    is_published = models.BooleanField(default=True)

    def publish_advert(self) -> None:
        self.is_published = True
        self.save(update_fields=["is_published"])


class JobApplication(AuditableModel):
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=30)
    linkedin_url = models.URLField()
    github_url = models.URLField()
    website = models.URLField(blank=True, null=True)
    experience_years = models.CharField(max_length=10, choices=YearOfExperience)
    cover_letter = models.CharField(max_length=255, blank=True, null=True)
    job_advert = models.ForeignKey(
        JobAdvert, related_name="applications", on_delete=models.CASCADE
    )

    class Meta:
        ordering = ("created_at",)
