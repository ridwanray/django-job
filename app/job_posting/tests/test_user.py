import pytest
from django.contrib.auth.hashers import check_password
from django.urls import reverse
from job_posting.models import User
from rest_framework.test import APIClient

pytestmark = pytest.mark.django_db


class TestUserRegistration:
    create_user_url = reverse("user:user-list")

    def test_create_user(self, api_client: APIClient):
        data = {"email": "ray@gmail.co", "password": "12345"}

        response = api_client.post(self.create_user_url, data)
        assert response.status_code == 200
        user_object = User.objects.get(email=data["email"])
        assert check_password(data["password"], user_object.password)

    def test_create_user_duplicate_email(
        self, api_client: APIClient, user_instance: User
    ):
        data = {"email": user_instance.email, "password": "xyzzyx"}
        response = api_client.post(self.create_user_url, data)
        assert response.status_code == 400
        assert "email" in response.json()
