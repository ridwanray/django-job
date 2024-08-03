import pytest
from django.urls import reverse
from job_posting.models import User
from pytest_factoryboy import register
from rest_framework.test import APIClient

from .factories import UserFactory

register(UserFactory)


def api_client_with_credentials(token: str, api_client):
    """Sets a credential on the default api client"""
    return api_client.credentials(HTTP_AUTHORIZATION="Token " + token)


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user_instance(db, user_factory):
    return user_factory.create()


@pytest.fixture
def auth_user_password() -> str:
    """returns user's password to be used in authentication"""
    return "TestPass@1"


@pytest.fixture
def authenticate_user(api_client, user_instance: User, auth_user_password: str) -> str:
    """Returns token needed for authentication"""

    url = reverse("auth:auth-login")
    data = {
        "email": user_instance.email,
        "password": auth_user_password,
    }
    response = api_client.post(url, data)
    token: str = response.json()["token"]
    return token
