from unittest.mock import Mock, patch

import pytest
from django.urls import reverse
from job_posting.models import JobAdvert
from rest_framework.test import APIClient

from .conftest import api_client_with_credentials
from .factories import JobAdvertFactory, JobApplicationFactory

pytestmark = pytest.mark.django_db


class TestJobAdvert:

    list_job_advert_url = reverse("job_posting:jobadvert-list")

    def test_post_advert(self, api_client: APIClient, authenticate_user):

        data = {
            "title": "string",
            "company_name": "string",
            "employment_type": "Full Time",
            "experience_level": "Entry Level",
            "description": "string",
            "location": "string",
        }

        api_client_with_credentials(authenticate_user, api_client)
        response = api_client.post(self.list_job_advert_url, data)
        assert response.status_code == 201
        returned_json: dict = response.json()
        assert "id" in returned_json
        assert returned_json["is_published"]

    def test_list_adverts(self, api_client: APIClient):
        JobAdvertFactory.create_batch(5)
        response = api_client.get(self.list_job_advert_url)
        assert response.status_code == 200
        assert response.json()["total"] == 5

    def test_retrieve_an_advert(self, api_client: APIClient):
        job_advert = JobAdvertFactory(title="Eng", company_name="ABC")
        JobApplicationFactory.create_batch(3, job_advert=job_advert)

        url = reverse("job_posting:jobadvert-detail", kwargs={"pk": str(job_advert.id)})
        response = api_client.get(url)
        assert response.status_code == 200
        returned_json = response.json()
        assert returned_json["applicant_count"] == 3
        assert returned_json["title"] == job_advert.title
        assert returned_json["company_name"] == job_advert.company_name

    def test_update_an_advert(self, api_client: APIClient,authenticate_user):
        job_advert = JobAdvertFactory(title="Eng", company_name="ABC")
        data = {
            "title": "Backend Eng"
        }
        url = reverse("job_posting:jobadvert-detail", kwargs={"pk": str(job_advert.id)})
        api_client_with_credentials(authenticate_user, api_client)
        response = api_client.patch(url, data)
        assert response.status_code == 200
        returned_json = response.json()
        assert returned_json["title"] == data["title"]


    def test_publish_advert(self, api_client: APIClient, authenticate_user):
        job_advert: JobAdvert = JobAdvertFactory(is_published=False)
        api_client_with_credentials(authenticate_user, api_client)
        url = reverse(
            "job_posting:jobadvert-publish", kwargs={"pk": str(job_advert.id)}
        )
        response = api_client.post(url)
        assert response.status_code == 200
        job_advert.refresh_from_db()
        assert job_advert.is_published

    def test_unpublish_advert(self, api_client: APIClient, authenticate_user):
        job_advert: JobAdvert = JobAdvertFactory(is_published=True)
        api_client_with_credentials(authenticate_user, api_client)
        url = reverse(
            "job_posting:jobadvert-unpublish", kwargs={"pk": str(job_advert.id)}
        )
        response = api_client.post(url)
        assert response.status_code == 200
        job_advert.refresh_from_db()
        assert not job_advert.is_published

    def test_delete_unpublished_advert(self, api_client: APIClient, authenticate_user):
        job_advert: JobAdvert = JobAdvertFactory(is_published=False)
        api_client_with_credentials(authenticate_user, api_client)
        url = reverse("job_posting:jobadvert-detail", kwargs={"pk": str(job_advert.id)})
        response = api_client.delete(url)
        assert response.status_code == 204

    def test_delete_published_advert(self, api_client: APIClient, authenticate_user):
        job_advert: JobAdvert = JobAdvertFactory(is_published=True)
        api_client_with_credentials(authenticate_user, api_client)
        url = reverse("job_posting:jobadvert-detail", kwargs={"pk": str(job_advert.id)})
        response = api_client.delete(url)
        assert response.status_code == 400
        assert "error" in response.json()

    def test_apply_for_advert(self, api_client: APIClient):
        job_advert: JobAdvert = JobAdvertFactory(is_published=True)
        data = {
            "first_name": "string",
            "last_name": "string",
            "email": "user@example.com",
            "phone": "string",
            "linkedin_url": "http://127.0.0.1:8000",
            "github_url": "http://127.0.0.1:8000",
            "website": "http://127.0.0.1:8000",
            "experience_years": "0-1",
            "cover_letter": "string",
        }
        url = reverse("job_posting:jobadvert-apply", kwargs={"pk": str(job_advert.id)})
        response = api_client.post(url, data)
        assert response.status_code == 200
        job_advert.refresh_from_db()
        assert job_advert.applications.count() == 1

    def test_apply_for_unpublished_advert(
        self, api_client: APIClient, authenticate_user
    ):
        job_advert: JobAdvert = JobAdvertFactory(is_published=False)

        data = {
            "first_name": "string",
            "last_name": "string",
            "email": "user@example.com",
            "phone": "string",
            "linkedin_url": "http://127.0.0.1:8000",
            "github_url": "http://127.0.0.1:8000",
            "website": "http://127.0.0.1:8000",
            "experience_years": "0-1",
            "cover_letter": "string",
        }
        url = reverse("job_posting:jobadvert-apply", kwargs={"pk": str(job_advert.id)})
        api_client_with_credentials(authenticate_user, api_client)
        response = api_client.post(url, data)
        assert response.status_code == 400
        assert "error" in response.json()

    def test_retrieve_advert_applications(
        self, api_client: APIClient, authenticate_user
    ):
        job_advert: JobAdvert = JobAdvertFactory()
        JobApplicationFactory.create_batch(2, job_advert=job_advert)
        api_client_with_credentials(authenticate_user, api_client)
        url = reverse(
            "job_posting:jobadvert-applications", kwargs={"pk": str(job_advert.id)}
        )
        response = api_client.get(url)
        assert response.status_code == 200
        assert response.json()["total"] == 2

    @patch("job_posting.tasks.schedule_job_advert.apply_async")
    def test_schedule_advert(
        self, mocked_scheduler: Mock, api_client: APIClient, authenticate_user
    ):
        job_advert: JobAdvert = JobAdvertFactory(is_published=False)
        api_client_with_credentials(authenticate_user, api_client)
        url = reverse(
            "job_posting:jobadvert-schedule-advert", kwargs={"pk": str(job_advert.id)}
        )
        data = {"date_time": "2024-08-03T08:01:04.527Z"}
        response = api_client.post(url, data)
        assert response.status_code == 200
        mocked_scheduler.assert_called_once()
        keyword_args: dict = mocked_scheduler.call_args.kwargs
        assert keyword_args.get("eta")
        assert keyword_args.get("kwargs").get("job_id") == job_advert.id

    def test_schedule_published_advert(self, api_client: APIClient, authenticate_user):
        job_advert: JobAdvert = JobAdvertFactory(is_published=True)
        api_client_with_credentials(authenticate_user, api_client)
        url = reverse(
            "job_posting:jobadvert-schedule-advert", kwargs={"pk": str(job_advert.id)}
        )
        data = {"date_time": "2024-08-03T08:01:04.527Z"}
        response = api_client.post(url, data)
        assert response.status_code == 400
        assert "error" in response.json()
