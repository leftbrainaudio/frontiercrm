"""Comprehensive tests for file upload endpoints.

Covers: CRUD, direct upload (mock S3), presign upload (mock S3),
download URL (mock S3), associate, and multi-tenant isolation.

S3 mocking patches ``apps.files.views._get_s3_client`` with a MagicMock.
"""

from __future__ import annotations

import io
import uuid
from unittest.mock import MagicMock, patch

import pytest
from django.utils import timezone


# ── Helpers ───────────────────────────────────────────────────────────────────


def create_file(tenant_id, **overrides):
    """Factory helper — creates a FileUpload directly via ORM."""
    from apps.files.models import FileUpload

    defaults = dict(
        tenant_id=tenant_id,
        original_filename="report.pdf",
        file_key=f"{tenant_id}/abc-123.pdf",
        file_size=2048,
        mime_type="application/pdf",
        bucket="frontiercrm-uploads",
        entity_type="",
        entity_id=None,
        uploaded_by_id=None,
        is_temporary=False,
    )
    defaults.update(overrides)
    return FileUpload.objects.create(**defaults)


def file_record_data(**overrides):
    """Return a POST-able payload for creating a file record (not upload)."""
    data = dict(
        original_filename="invoice.pdf",
        file_key="uploads/invoice.pdf",
        file_size=4096,
        mime_type="application/pdf",
    )
    data.update(overrides)
    return data


# ── CRUD ──────────────────────────────────────────────────────────────────────


class TestFileCRUD:
    """Create, Read, List, Delete file records."""

    BASE_URL = "/api/files/"

    def test_list_empty(self, auth_client, db):
        resp = auth_client.get(self.BASE_URL)
        assert resp.status_code == 200
        assert resp.json()["results"] == []

    def test_list_with_data(self, auth_client, user, db):
        create_file(tenant_id=user.tenant_id)
        create_file(tenant_id=user.tenant_id, original_filename="second.png")
        resp = auth_client.get(self.BASE_URL)
        assert resp.status_code == 200
        assert len(resp.json()["results"]) == 2

    def test_create_record(self, auth_client, user, db):
        """Test creating a file upload record (not actual upload)."""
        payload = file_record_data()
        resp = auth_client.post(self.BASE_URL, payload, format="json")
        assert resp.status_code == 201
        data = resp.json()
        assert data["original_filename"] == "invoice.pdf"
        assert data["file_key"] == "uploads/invoice.pdf"
        assert data["file_size"] == 4096
        assert data["tenant_id"] == str(user.tenant_id)

    def test_retrieve(self, auth_client, user, db):
        f = create_file(tenant_id=user.tenant_id)
        resp = auth_client.get(f"{self.BASE_URL}{f.id}/")
        assert resp.status_code == 200
        assert resp.json()["original_filename"] == "report.pdf"

    def test_retrieve_not_found(self, auth_client, db):
        resp = auth_client.get(f"{self.BASE_URL}{uuid.uuid4()}/")
        assert resp.status_code == 404

    def test_delete(self, auth_client, user, db):
        f = create_file(tenant_id=user.tenant_id)
        resp = auth_client.delete(f"{self.BASE_URL}{f.id}/")
        assert resp.status_code == 204
        resp = auth_client.get(f"{self.BASE_URL}{f.id}/")
        assert resp.status_code == 404

    def test_update_not_partial_fails(self, auth_client, user, db):
        """PUT (full update) fails with 400 because it requires all fields."""
        f = create_file(tenant_id=user.tenant_id)
        resp = auth_client.put(
            f"{self.BASE_URL}{f.id}/",
            {"original_filename": "override.pdf"},
            format="json",
        )
        # PUT with partial data is a bad request
        assert resp.status_code == 400


# ── Upload action ─────────────────────────────────────────────────────────────


class TestFileUpload:
    """POST /api/files/upload/ — direct upload to S3."""

    BASE_URL = "/api/files/"

    def test_upload_success(self, auth_client, user, db):
        """Upload a file with mock S3."""
        from django.core.files.uploadedfile import SimpleUploadedFile

        mock_s3 = MagicMock()
        with patch("apps.files.views._get_s3_client", return_value=mock_s3):
            uploaded = SimpleUploadedFile(
                "report.pdf",
                b"fake pdf content",
                content_type="application/pdf",
            )
            resp = auth_client.post(
                f"{self.BASE_URL}upload/",
                {"file": uploaded, "entity_type": "contact", "entity_id": str(uuid.uuid4())},
                format="multipart",
            )
        assert resp.status_code == 201
        data = resp.json()
        assert data["original_filename"] == "report.pdf"
        assert data["file_size"] == 16  # bytes
        assert data["mime_type"] == "application/pdf"
        assert data["tenant_id"] == str(user.tenant_id)
        assert data["entity_type"] == "contact"
        # verify S3 client was called
        mock_s3.upload_fileobj.assert_called_once()
        call_args = mock_s3.upload_fileobj.call_args
        assert call_args[0][1] == "frontiercrm-uploads"  # bucket

    def test_upload_with_named_file(self, auth_client, user, db):
        """Upload with a named file preserves original_filename."""
        from django.core.files.uploadedfile import SimpleUploadedFile

        mock_s3 = MagicMock()
        with patch("apps.files.views._get_s3_client", return_value=mock_s3):
            uploaded = SimpleUploadedFile(
                "contract.pdf",
                b"contract content here",
                content_type="application/pdf",
            )
            resp = auth_client.post(
                f"{self.BASE_URL}upload/",
                {"file": uploaded},
                format="multipart",
            )
        assert resp.status_code == 201
        assert resp.json()["original_filename"] == "contract.pdf"
        assert resp.json()["mime_type"] == "application/pdf"

    def test_upload_missing_file(self, auth_client, db):
        """Upload without a file returns 400."""
        mock_s3 = MagicMock()
        with patch("apps.files.views._get_s3_client", return_value=mock_s3):
            resp = auth_client.post(f"{self.BASE_URL}upload/", {}, format="multipart")
        assert resp.status_code == 400
        assert "file required" in resp.json()["error"].lower()

    def test_upload_oversized(self, auth_client, db):
        """File exceeding FILE_UPLOAD_MAX_SIZE returns 400."""
        from django.conf import settings

        huge = b"x" * (settings.FILE_UPLOAD_MAX_SIZE + 1)
        mock_s3 = MagicMock()
        with patch("apps.files.views._get_s3_client", return_value=mock_s3):
            uploaded = io.BytesIO(huge)
            uploaded.name = "huge.bin"
            resp = auth_client.post(
                f"{self.BASE_URL}upload/",
                {"file": uploaded},
                format="multipart",
            )
        assert resp.status_code == 400
        assert "too large" in resp.json()["error"].lower()
        mock_s3.upload_fileobj.assert_not_called()

    def test_upload_s3_failure_returns_500(self, auth_client, db):
        """If S3 client raises, view still raises (500)."""
        mock_s3 = MagicMock()
        mock_s3.upload_fileobj.side_effect = Exception("S3 down")
        with patch("apps.files.views._get_s3_client", return_value=mock_s3):
            uploaded = io.BytesIO(b"data")
            uploaded.name = "fail.txt"
            with pytest.raises(Exception):
                auth_client.post(
                    f"{self.BASE_URL}upload/",
                    {"file": uploaded},
                    format="multipart",
                )


# ── Presign upload ────────────────────────────────────────────────────────────


class TestFilePresignUpload:
    """POST /api/files/presign_upload/ — presigned URL generation."""

    BASE_URL = "/api/files/"

    def test_presign_upload_success(self, auth_client, db):
        mock_s3 = MagicMock()
        mock_s3.generate_presigned_url.return_value = "https://presigned.example.com/upload"
        with patch("apps.files.views._get_s3_client", return_value=mock_s3):
            resp = auth_client.post(
                f"{self.BASE_URL}presign_upload/",
                {"filename": "photo.png", "content_type": "image/png"},
                format="json",
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["presigned_url"] == "https://presigned.example.com/upload"
        assert data["bucket"] == "frontiercrm-uploads"
        assert "file_key" in data
        # verify the S3 call
        mock_s3.generate_presigned_url.assert_called_once_with(
            "put_object",
            Params={
                "Bucket": "frontiercrm-uploads",
                "Key": data["file_key"],
                "ContentType": "image/png",
            },
            ExpiresIn=3600,
        )

    def test_presign_upload_defaults(self, auth_client, db):
        """Defaults: filename='upload', content_type='application/octet-stream'."""
        mock_s3 = MagicMock()
        mock_s3.generate_presigned_url.return_value = "https://presigned.example.com/up"
        with patch("apps.files.views._get_s3_client", return_value=mock_s3):
            resp = auth_client.post(
                f"{self.BASE_URL}presign_upload/",
                {},
                format="json",
            )
        assert resp.status_code == 200
        assert "presigned_url" in resp.json()
        call_kwargs = mock_s3.generate_presigned_url.call_args[1]
        assert call_kwargs["Params"]["ContentType"] == "application/octet-stream"

    def test_presign_key_uses_tenant_prefix(self, auth_client, user, db):
        mock_s3 = MagicMock()
        mock_s3.generate_presigned_url.return_value = "https://presigned.example.com/up"
        with patch("apps.files.views._get_s3_client", return_value=mock_s3):
            resp = auth_client.post(
                f"{self.BASE_URL}presign_upload/",
                {"filename": "doc.pdf"},
                format="json",
            )
        file_key = resp.json()["file_key"]
        assert file_key.startswith(f"{user.tenant_id}/")


# ── Download URL ──────────────────────────────────────────────────────────────


class TestFileDownload:
    """GET /api/files/{id}/download_url/."""

    BASE_URL = "/api/files/"

    def test_download_url_success(self, auth_client, user, db):
        f = create_file(tenant_id=user.tenant_id)
        mock_s3 = MagicMock()
        mock_s3.generate_presigned_url.return_value = "https://download.example.com/file"
        with patch("apps.files.views._get_s3_client", return_value=mock_s3):
            resp = auth_client.get(f"{self.BASE_URL}{f.id}/download_url/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["url"] == "https://download.example.com/file"
        assert data["filename"] == "report.pdf"
        mock_s3.generate_presigned_url.assert_called_once_with(
            "get_object",
            Params={"Bucket": "frontiercrm-uploads", "Key": f.file_key},
            ExpiresIn=3600,
        )

    def test_download_url_other_tenant(self, auth_client, user, db):
        """Cannot get download URL for another tenant's file."""
        other_tenant = uuid.uuid4()
        f = create_file(tenant_id=other_tenant)
        mock_s3 = MagicMock()
        with patch("apps.files.views._get_s3_client", return_value=mock_s3):
            resp = auth_client.get(f"{self.BASE_URL}{f.id}/download_url/")
        assert resp.status_code == 404
        mock_s3.generate_presigned_url.assert_not_called()

    def test_download_url_not_found(self, auth_client, db):
        mock_s3 = MagicMock()
        with patch("apps.files.views._get_s3_client", return_value=mock_s3):
            resp = auth_client.get(f"{self.BASE_URL}{uuid.uuid4()}/download_url/")
        assert resp.status_code == 404
        mock_s3.generate_presigned_url.assert_not_called()


# ── Associate ─────────────────────────────────────────────────────────────────


class TestFileAssociate:
    """POST /api/files/{id}/associate/ — attach file to entity."""

    BASE_URL = "/api/files/"

    def test_associate_to_entity(self, auth_client, user, db):
        f = create_file(tenant_id=user.tenant_id, entity_type="", entity_id=None)
        entity_id = uuid.uuid4()
        resp = auth_client.post(
            f"{self.BASE_URL}{f.id}/associate/",
            {"entity_type": "contact", "entity_id": str(entity_id)},
            format="json",
        )
        assert resp.status_code == 200
        assert resp.json()["entity_type"] == "contact"
        assert resp.json()["entity_id"] == str(entity_id)
        f.refresh_from_db()
        assert f.entity_type == "contact"
        assert f.entity_id == entity_id

    def test_associate_partial_update(self, auth_client, user, db):
        existing_id = uuid.uuid4()
        f = create_file(tenant_id=user.tenant_id, entity_type="deal", entity_id=existing_id)
        # update only entity_type
        resp = auth_client.post(
            f"{self.BASE_URL}{f.id}/associate/",
            {"entity_type": "contact"},
            format="json",
        )
        assert resp.status_code == 200
        assert resp.json()["entity_type"] == "contact"
        assert resp.json()["entity_id"] == str(existing_id)  # unchanged

    def test_associate_other_tenant(self, auth_client, user, db):
        """Cannot associate another tenant's file."""
        other_tenant = uuid.uuid4()
        f = create_file(tenant_id=other_tenant)
        resp = auth_client.post(
            f"{self.BASE_URL}{f.id}/associate/",
            {"entity_type": "contact", "entity_id": str(uuid.uuid4())},
            format="json",
        )
        assert resp.status_code == 404

    def test_associate_not_found(self, auth_client, db):
        resp = auth_client.post(
            f"{self.BASE_URL}{uuid.uuid4()}/associate/",
            {"entity_type": "contact", "entity_id": str(uuid.uuid4())},
            format="json",
        )
        assert resp.status_code == 404


# ── Multi-tenant isolation ────────────────────────────────────────────────────


class TestFileTenantIsolation:
    """Tenants must not see each other's files."""

    BASE_URL = "/api/files/"

    def test_list_isolation(self, auth_client, user, db):
        other_tenant = uuid.uuid4()
        create_file(tenant_id=user.tenant_id, original_filename="mine.txt")
        create_file(tenant_id=other_tenant, original_filename="theirs.txt")
        resp = auth_client.get(self.BASE_URL)
        names = [f["original_filename"] for f in resp.json()["results"]]
        assert "mine.txt" in names
        assert "theirs.txt" not in names

    def test_retrieve_isolation(self, auth_client, user, db):
        other_tenant = uuid.uuid4()
        f = create_file(tenant_id=other_tenant)
        resp = auth_client.get(f"{self.BASE_URL}{f.id}/")
        assert resp.status_code == 404

    def test_delete_isolation(self, auth_client, user, db):
        other_tenant = uuid.uuid4()
        f = create_file(tenant_id=other_tenant)
        resp = auth_client.delete(f"{self.BASE_URL}{f.id}/")
        assert resp.status_code == 404

    def test_create_sets_own_tenant_and_uploader(self, auth_client, user, db):
        payload = file_record_data()
        resp = auth_client.post(self.BASE_URL, payload, format="json")
        assert resp.status_code == 201
        assert resp.json()["tenant_id"] == str(user.tenant_id)