"""Tests for core models — base model, tenant scoping, soft delete."""

from __future__ import annotations

import uuid

import pytest


class TestTimeStampedModel:
    """Verify base timestamp and soft-delete behavior."""

    def test_auto_timestamps(self, db):
        """Should set created_at on creation and update updated_at."""
        from apps.notes.models import Note

        note = Note.objects.create(
            tenant_id=uuid.uuid4(),
            entity_type="contact",
            entity_id=uuid.uuid4(),
            title="Test Note",
        )
        assert note.created_at is not None
        assert note.updated_at is not None
        assert note.deleted_at is None

    def test_soft_delete(self, db):
        """Soft delete should set deleted_at and mark as deleted."""
        from apps.notes.models import Note

        note = Note.objects.create(
            tenant_id=uuid.uuid4(),
            entity_type="contact",
            entity_id=uuid.uuid4(),
            title="To Delete",
        )
        note.soft_delete()
        assert note.is_deleted is True
        assert note.deleted_at is not None


class TestTenantIsolation:
    """Verify tenant_id is required and scoped."""

    def test_tenant_id_required(self, db):
        """TenantScopedModel requires tenant_id."""
        from apps.contacts.models import Contact

        with pytest.raises(Exception):
            Contact.objects.create(
                first_name="No",
                last_name="Tenant",
                email="notenant@test.com",
            )

    def test_tenant_scoping(self, db):
        """Records from different tenants should be isolated."""
        from apps.contacts.models import Contact

        tid_a = uuid.uuid4()
        tid_b = uuid.uuid4()

        Contact.objects.create(tenant_id=tid_a, first_name="Alice", last_name="A")
        Contact.objects.create(tenant_id=tid_b, first_name="Bob", last_name="B")

        assert Contact.objects.filter(tenant_id=tid_a).count() == 1
        assert Contact.objects.filter(tenant_id=tid_b).count() == 1
        assert Contact.objects.count() == 2

    def test_contact_str(self, db):
        """String representation of Contact."""
        from apps.contacts.models import Contact

        c = Contact.objects.create(
            tenant_id=uuid.uuid4(),
            first_name="John",
            last_name="Doe",
            email="john@example.com",
        )
        assert str(c) == "John Doe"
        assert c.full_name == "John Doe"
