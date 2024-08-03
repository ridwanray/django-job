import factory
from faker import Faker
from job_posting.models import JobAdvert, JobApplication, User

fake = Faker()


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    email = factory.Sequence(lambda n: "person{}@example.com".format(n))
    password = factory.PostGenerationMethodCall("set_password", "TestPass@1")


class JobAdvertFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = JobAdvert

    title = fake.text(max_nb_chars=20)
    company_name = fake.text(max_nb_chars=20)
    employment_type = factory.Iterator(["Full Time", "Contract"])
    experience_level = factory.Iterator(["Entry Level", "Senior"])
    description = fake.text(max_nb_chars=20)
    location = fake.text(max_nb_chars=20)


class JobApplicationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = JobApplication

    first_name = fake.text(max_nb_chars=20)
    last_name = fake.text(max_nb_chars=20)
    email = fake.email()
    phone = fake.phone_number()
    linkedin_url = fake.uri()
    github_url = fake.uri()
    website = fake.uri()
    experience_years = factory.Iterator(["0-1", "1-2"])
