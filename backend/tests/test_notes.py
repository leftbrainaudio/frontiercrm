"""Tests for notes API endpoints."""

from __future__ import annotations

import uuid

from apps.notes.models import Note


class TestNoteAPI:
    """Note CRUD endpoint tests."""

    BASE_URL = "/api/notes/"

    def test_list_notes_empty(self, auth_client, db):
        resp = auth_client.get(self.BASE_URL)
        assert resp.status_code == 200
        data = resp.json()
        assert "results" in data
        assert data["count"] == 0

    def test_list_notes(self, auth_client, user, db):
        Note.objects.create(
            tenant_id=user.tenant_id,
            entity_type="contact",
            entity_id=uuid.uuid4(),
            title="Note one",
            content="Content one",
        )
        Note.objects.create(
            tenant_id=user.tenant_id,
            entity_type="deal",
            entity_id=uuid.uuid4(),
            title="Note two",
            content="Content two",
        )
        resp = auth_client.get(self.BASE_URL)
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 2
        assert len(data["results"]) == 2

    def test_create_note(self, auth_client, user, db):
        resp = auth_client.post(
            self.BASE_URL,
            {
                "title": "Test Note",
                "content": "Hello world",
                "entity_type": "contact",
                "entity_id": str(uuid.uuid4()),
            },
            format="json",
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["title"] == "Test Note"
        assert data["content"] == "Hello world"
        assert data["tenant_id"] == str(user.tenant_id)
        assert "id" in data
        assert "created_at" in data
        assert Note.objects.count() == 1

    def test_create_note_with_content_html(self, auth_client, user, db):
        resp = auth_client.post(
            self.BASE_URL,
            {
                "title": "HTML Note",
                "content": "Plain text",
                "content_html": "<p>Rich text</p>",
                "entity_type": "contact",
                "entity_id": str(uuid.uuid4()),
            },
            format="json",
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["content_html"] == "<p>Rich text</p>"

    def test_create_note_sets_owner_id(self, auth_client, user, db):
        resp = auth_client.post(
            self.BASE_URL,
            {
                "title": "Owned note",
                "content": "Content",
                "entity_type": "contact",
                "entity_id": str(uuid.uuid4()),
            },
            format="json",
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["owner_id"] == str(user.id)

    def test_get_note_detail(self, auth_client, user, db):
        entity_id = uuid.uuid4()
        note = Note.objects.create(
            tenant_id=user.tenant_id,
            entity_type="contact",
            entity_id=entity_id,
            title="Detail note",
            content="Detail content",
            content_html="<p>Detail content</p>",
            is_pinned=True,
        )
        resp = auth_client.get(f"{self.BASE_URL}{note.id}/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == str(note.id)
        assert data["title"] == "Detail note"
        assert data["content"] == "Detail content"
        assert data["content_html"] == "<p>Detail content</p>"
        assert data["entity_type"] == "contact"
        assert data["entity_id"] == str(entity_id)
        assert data["is_pinned"] is True

    def test_update_note(self, auth_client, user, db):
        note = Note.objects.create(
            tenant_id=user.tenant_id,
            entity_type="contact",
            entity_id=uuid.uuid4(),
            title="Original",
            content="Original content",
        )
        resp = auth_client.patch(
            f"{self.BASE_URL}{note.id}/",
            {"title": "Updated", "content": "Updated content"},
            format="json",
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["title"] == "Updated"
        assert data["content"] == "Updated content"
        assert data["id"] == str(note.id)

    def test_update_note_pin(self, auth_client, user, db):
        note = Note.objects.create(
            tenant_id=user.tenant_id,
            entity_type="contact",
            entity_id=uuid.uuid4(),
            title="Pin test",
            is_pinned=False,
        )
        resp = auth_client.patch(
            f"{self.BASE_URL}{note.id}/",
            {"is_pinned": True},
            format="json",
        )
        assert resp.status_code == 200
        assert resp.json()["is_pinned"] is True

    def test_delete_note_returns_204(self, auth_client, user, db):
        note = Note.objects.create(
            tenant_id=user.tenant_id,
            entity_type="contact",
            entity_id=uuid.uuid4(),
            title="To Delete",
        )
        resp = auth_client.delete(f"{self.BASE_URL}{note.id}/")
        assert resp.status_code == 204
        assert Note.objects.count() == 0

    def test_delete_nonexistent_returns_404(self, auth_client, db):
        resp = auth_client.delete(f"{self.BASE_URL}{uuid.uuid4()}/")
        assert resp.status_code == 404

    def test_filter_by_entity_type(self, auth_client, user, db):
        Note.objects.create(
            tenant_id=user.tenant_id,
            entity_type="contact",
            entity_id=uuid.uuid4(),
            title="Contact note",
        )
        Note.objects.create(
            tenant_id=user.tenant_id,
            entity_type="deal",
            entity_id=uuid.uuid4(),
            title="Deal note",
        )
        resp = auth_client.get(f"{self.BASE_URL}?entity_type=deal")
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 1
        assert data["results"][0]["entity_type"] == "deal"

    def test_filter_by_entity_id(self, auth_client, user, db):
        target_entity_id = uuid.uuid4()
        Note.objects.create(
            tenant_id=user.tenant_id,
            entity_type="contact",
            entity_id=target_entity_id,
            title="Target note",
        )
        Note.objects.create(
            tenant_id=user.tenant_id,
            entity_type="contact",
            entity_id=uuid.uuid4(),
            title="Other note",
        )
        resp = auth_client.get(f"{self.BASE_URL}?entity_id={target_entity_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 1
        assert data["results"][0]["entity_id"] == str(target_entity_id)

    def test_filter_by_owner_id(self, auth_client, user, db):
        """Notes created via the API have owner_id set to the request user."""
        resp = auth_client.post(
            self.BASE_URL,
            {
                "title": "My note",
                "content": "My content",
                "entity_type": "contact",
                "entity_id": str(uuid.uuid4()),
            },
            format="json",
        )
        assert resp.status_code == 201
        my_note_id = resp.json()["id"]

        resp2 = auth_client.get(f"{self.BASE_URL}?owner_id={user.id}")
        assert resp2.status_code == 200
        data = resp2.json()
        assert data["count"] >= 1
        note_ids = [n["id"] for n in data["results"]]
        assert my_note_id in note_ids

    def test_filter_by_is_pinned(self, auth_client, user, db):
        Note.objects.create(
            tenant_id=user.tenant_id,
            entity_type="contact",
            entity_id=uuid.uuid4(),
            title="Pinned note",
            is_pinned=True,
        )
        Note.objects.create(
            tenant_id=user.tenant_id,
            entity_type="contact",
            entity_id=uuid.uuid4(),
            title="Unpinned note",
            is_pinned=False,
        )
        resp = auth_client.get(f"{self.BASE_URL}?is_pinned=true")
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 1
        assert data["results"][0]["is_pinned"] is True

    def test_search_by_title(self, auth_client, user, db):
        Note.objects.create(
            tenant_id=user.tenant_id,
            entity_type="contact",
            entity_id=uuid.uuid4(),
            title="Unique widget specification",
            content="Something about widgets",
        )
        Note.objects.create(
            tenant_id=user.tenant_id,
            entity_type="contact",
            entity_id=uuid.uuid4(),
            title="Other note",
            content="No match here",
        )
        resp = auth_client.get(f"{self.BASE_URL}?search=Unique")
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 1
        assert "Unique" in data["results"][0]["title"]

    def test_search_by_content(self, auth_client, user, db):
        Note.objects.create(
            tenant_id=user.tenant_id,
            entity_type="contact",
            entity_id=uuid.uuid4(),
            title="Important",
            content="This contains a secret keyword",
        )
        Note.objects.create(
            tenant_id=user.tenant_id,
            entity_type="contact",
            entity_id=uuid.uuid4(),
            title="Boring",
            content="Nothing special",
        )
        resp = auth_client.get(f"{self.BASE_URL}?search=secret+keyword")
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 1
        assert data["results"][0]["title"] == "Important"

    def test_search_returns_empty_for_no_match(self, auth_client, user, db):
        Note.objects.create(
            tenant_id=user.tenant_id,
            entity_type="contact",
            entity_id=uuid.uuid4(),
            title="Present",
            content="Here",
        )
        resp = auth_client.get(f"{self.BASE_URL}?search=xyzzy_nonexistent")
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 0

    def test_note_str_representation(self, db, tenant_id):
        note_with_title = Note.objects.create(
            tenant_id=tenant_id,
            entity_type="contact",
            entity_id=uuid.uuid4(),
            title="My Title",
            content="Content",
        )
        assert str(note_with_title) == "My Title"

        note_empty_title = Note.objects.create(
            tenant_id=tenant_id,
            entity_type="contact",
            entity_id=uuid.uuid4(),
            title="",
            content="Content",
        )
        assert str(note_empty_title) == f"Note ({note_empty_title.id})"

        note_long_title = Note.objects.create(
            tenant_id=tenant_id,
            entity_type="contact",
            entity_id=uuid.uuid4(),
            title="A" * 100,
            content="Content",
        )
        assert len(str(note_long_title)) <= 50

    def test_multi_tenant_isolation(self, auth_client, user, db):
        Note.objects.create(
            tenant_id=uuid.uuid4(),
            entity_type="contact",
            entity_id=uuid.uuid4(),
            title="Other tenant note",
        )
        Note.objects.create(
            tenant_id=user.tenant_id,
            entity_type="contact",
            entity_id=uuid.uuid4(),
            title="My tenant note",
        )
        resp = auth_client.get(self.BASE_URL)
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 1
        for note in data["results"]:
            assert note["tenant_id"] == str(user.tenant_id)

    def test_access_other_tenant_note_returns_404(self, auth_client, user, db):
        other = Note.objects.create(
            tenant_id=uuid.uuid4(),
            entity_type="contact",
            entity_id=uuid.uuid4(),
            title="Other tenant",
        )
        resp = auth_client.get(f"{self.BASE_URL}{other.id}/")
        assert resp.status_code == 404

    def test_update_other_tenant_note_returns_404(self, auth_client, user, db):
        other = Note.objects.create(
            tenant_id=uuid.uuid4(),
            entity_type="contact",
            entity_id=uuid.uuid4(),
            title="Other tenant",
        )
        resp = auth_client.patch(
            f"{self.BASE_URL}{other.id}/",
            {"title": "Hacked"},
            format="json",
        )
        assert resp.status_code == 404

    def test_delete_other_tenant_note_returns_404(self, auth_client, user, db):
        other = Note.objects.create(
            tenant_id=uuid.uuid4(),
            entity_type="contact",
            entity_id=uuid.uuid4(),
            title="Other tenant",
        )
        resp = auth_client.delete(f"{self.BASE_URL}{other.id}/")
        assert resp.status_code == 404
