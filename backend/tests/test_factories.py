"""Tests for the core factories module."""

from __future__ import annotations

from apps.activities.models import Activity


class TestFactories:
    """Verify all factory_boy factories produce valid model instances."""

    def test_account_factory(self, db):
        account = AccountFactory()
        assert account.name
        assert account.tenant_id
        assert account.id

    def test_contact_factory(self, db):
        contact = ContactFactory()
        assert contact.first_name
        assert contact.last_name
        assert contact.email
        assert contact.tenant_id

    def test_pipeline_factory(self, db):
        pipeline = PipelineFactory()
        assert pipeline.name
        assert pipeline.tenant_id

    def test_stage_factory(self, db):
        stage = StageFactory()
        assert stage.name
        assert stage.pipeline_id
        assert stage.probability == 0.25

    def test_deal_factory(self, db):
        deal = DealFactory()
        assert deal.name
        assert deal.pipeline_id
        assert deal.stage_id
        assert deal.value == 10000.00

    def test_note_factory(self, db):
        note = NoteFactory()
        assert note.title
        assert note.content
        assert note.entity_type == "contact"

    def test_task_factory(self, db):
        task = TaskItemFactory()
        assert task.title
        assert task.tenant_id

    def test_activity_factory(self, db):
        activity = ActivityFactory()
        assert activity.activity_type == Activity.ActivityType.NOTE

    def test_email_factory(self, db):
        email = EmailMessageFactory()
        assert email.message_id
        assert email.subject

    def test_file_factory(self, db):
        f = FileUploadFactory()
        assert f.original_filename
        assert f.file_key

    def test_webhook_endpoint_factory(self, db):
        w = WebhookEndpointFactory()
        assert w.url
        assert w.secret

    def test_tenant_factory(self, db):
        t = TenantFactory()
        assert t.name
        assert t.id

    def test_team_factory(self, db):
        team = TeamFactory()
        assert team.name
        assert team.tenant_id

    def test_role_factory(self, db):
        role = RoleFactory()
        assert role.name
        assert role.tenant_id

    def test_membership_factory(self, db):
        membership = MembershipFactory()
        assert membership.user_id
        assert membership.tenant_id


from apps.core.factories import (  # noqa: E402
    AccountFactory,
    ActivityFactory,
    ContactFactory,
    DealFactory,
    EmailMessageFactory,
    FileUploadFactory,
    MembershipFactory,
    NoteFactory,
    PipelineFactory,
    RoleFactory,
    StageFactory,
    TaskItemFactory,
    TeamFactory,
    TenantFactory,
    WebhookEndpointFactory,
)
