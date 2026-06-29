"""Factory boy factories for all core models. Used for test fixtures."""

from __future__ import annotations

import uuid

import factory
from django.contrib.auth import get_user_model

from apps.activities.models import Activity
from apps.contacts.models import Account, Contact
from apps.email.models import EmailMessage
from apps.files.models import FileUpload
from apps.notes.models import Note
from apps.pipelines.models import Deal, Pipeline, Stage
from apps.tasks.models import TaskItem
from apps.teams.models import Membership, Role, Team, Tenant
from apps.webhooks.models import WebhookEndpoint, WebhookEvent

UserModel = get_user_model()


class TenantFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Tenant

    id = factory.LazyFunction(uuid.uuid4)
    name = factory.Sequence(lambda n: f"Tenant {n}")
    subdomain = factory.Sequence(lambda n: f"tenant-{n}")


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = UserModel

    id = factory.LazyFunction(uuid.uuid4)
    username = factory.Sequence(lambda n: f"user-{n}")
    email = factory.Sequence(lambda n: f"user-{n}@frontiercrm.com")
    password = factory.PostGenerationMethodCall("set_password", "testpass123")
    tenant_id = factory.LazyFunction(uuid.uuid4)
    timezone = "UTC"
    locale = "en-US"


class TeamFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Team

    id = factory.LazyFunction(uuid.uuid4)
    tenant = factory.SubFactory(TenantFactory)
    name = factory.Sequence(lambda n: f"Team {n}")


class RoleFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Role

    id = factory.LazyFunction(uuid.uuid4)
    tenant = factory.SubFactory(TenantFactory)
    name = factory.Sequence(lambda n: f"Role {n}")


class MembershipFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Membership

    id = factory.LazyFunction(uuid.uuid4)
    user = factory.SubFactory(UserFactory)
    tenant = factory.SubFactory(TenantFactory)
    is_owner = False


class AccountFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Account

    name = factory.Sequence(lambda n: f"Account {n}")
    domain = factory.Sequence(lambda n: f"acme-{n}.com")
    tenant_id = factory.LazyFunction(uuid.uuid4)


class ContactFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Contact

    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    email = factory.Sequence(lambda n: f"contact-{n}@example.com")
    tenant_id = factory.LazyFunction(uuid.uuid4)

    @factory.post_generation
    def account(self, create, extracted, **kwargs):
        if extracted:
            self.account = extracted


class PipelineFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Pipeline

    name = factory.Sequence(lambda n: f"Pipeline {n}")
    tenant_id = factory.LazyFunction(uuid.uuid4)
    is_default = False


class StageFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Stage

    pipeline = factory.SubFactory(PipelineFactory)
    name = factory.Sequence(lambda n: f"Stage {n}")
    display_order = factory.Sequence(lambda n: n)
    probability = 0.25
    tenant_id = factory.LazyFunction(uuid.uuid4)


class DealFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Deal

    name = factory.Sequence(lambda n: f"Deal {n}")
    pipeline = factory.SubFactory(PipelineFactory)
    stage = factory.SubFactory(StageFactory)
    value = 10000.00
    tenant_id = factory.LazyFunction(uuid.uuid4)


class NoteFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Note

    title = factory.Sequence(lambda n: f"Note {n}")
    content = factory.Faker("text", max_nb_chars=200)
    entity_type = "contact"
    entity_id = factory.LazyFunction(uuid.uuid4)
    tenant_id = factory.LazyFunction(uuid.uuid4)


class TaskItemFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = TaskItem

    title = factory.Sequence(lambda n: f"Task {n}")
    tenant_id = factory.LazyFunction(uuid.uuid4)


class ActivityFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Activity

    activity_type = Activity.ActivityType.NOTE
    title = factory.Sequence(lambda n: f"Activity {n}")
    entity_type = "contact"
    entity_id = factory.LazyFunction(uuid.uuid4)
    tenant_id = factory.LazyFunction(uuid.uuid4)


class EmailMessageFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = EmailMessage

    message_id = factory.Sequence(lambda n: f"msg-{n}")
    thread_id = factory.Sequence(lambda n: f"thread-{n}")
    direction = EmailMessage.EmailDirection.INBOUND
    from_email = factory.Sequence(lambda n: f"sender-{n}@example.com")
    to_emails = ["recipient@example.com"]
    subject = factory.Sequence(lambda n: f"Email Subject {n}")
    body_text = factory.Faker("text", max_nb_chars=200)
    sent_at = factory.Faker("date_time")
    tenant_id = factory.LazyFunction(uuid.uuid4)


class FileUploadFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = FileUpload

    original_filename = factory.Sequence(lambda n: f"file-{n}.pdf")
    file_key = factory.Sequence(lambda n: f"uploads/{uuid.uuid4()}.pdf")
    file_size = 1024
    mime_type = "application/pdf"
    tenant_id = factory.LazyFunction(uuid.uuid4)


class WebhookEndpointFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = WebhookEndpoint

    url = factory.Sequence(lambda n: f"https://hooks.example.com/{n}")
    secret = "test-secret-123"
    events = ["contact.created", "deal.updated"]
    tenant_id = factory.LazyFunction(uuid.uuid4)


class WebhookEventFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = WebhookEvent

    endpoint = factory.SubFactory(WebhookEndpointFactory)
    event_type = "contact.created"
    payload = {"event": "test"}
    tenant_id = factory.LazyFunction(uuid.uuid4)
