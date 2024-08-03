from celery import shared_task

from .models import JobAdvert


@shared_task()
def schedule_job_advert(job_id):
    """Publish an advert at the set time"""
    job_post = JobAdvert.objects.get(id=job_id)
    job_post.publish_advert()
