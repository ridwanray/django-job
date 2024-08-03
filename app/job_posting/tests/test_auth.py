import pytest
from django.urls import reverse
from job_posting.models import User
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from .conftest import api_client_with_credentials

pytestmark = pytest.mark.django_db


class TestUserAuth:
    login_url = reverse("auth:auth-login")
    logout_url = reverse("auth:auth-logout")

    def test_login(
        self, api_client: APIClient, user_instance: User, auth_user_password
    ):
        data = {"email": user_instance.email, "password": auth_user_password}
        response = api_client.post(self.login_url, data)
        assert response.status_code == 200
        assert "token" in response.json()

    def test_login_invalid_credentials(
        self,
        api_client: APIClient,
        user_instance: User,
    ):
        data = {"email": user_instance.email, "password": "a random password"}
        response = api_client.post(self.login_url, data)
        assert response.status_code == 400
        assert "error" in response.json()

    def test_logout(self, api_client: APIClient, user_instance: User):
        token, _ = Token.objects.get_or_create(user=user_instance)
        api_client_with_credentials(token.key, api_client)
        response = api_client.post(self.logout_url)
        assert response.status_code == 200

    def test_logout_invalid_token(self, api_client: APIClient):
        token = "a-random-token"
        api_client_with_credentials(token, api_client)
        response = api_client.post(self.logout_url)
        assert response.status_code == 401
