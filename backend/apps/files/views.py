"""File upload with S3/R2 signed URLs."""

from __future__ import annotations

import uuid

from django.conf import settings
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from .models import FileUpload


def _get_s3_client():
    """Get a boto3 S3 client configured for R2-compatible storage."""
    import boto3

    return boto3.client(
        "s3",
        endpoint_url=settings.AWS_S3_ENDPOINT_URL or None,
        region_name=settings.AWS_S3_REGION_NAME,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    )


class FileUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = FileUpload
        exclude = ()
        read_only_fields = ("id", "tenant_id", "created_at", "updated_at")


class FileUploadViewSet(viewsets.ModelViewSet):
    queryset = FileUpload.objects.all()
    serializer_class = FileUploadSerializer

    def get_queryset(self):
        return FileUpload.objects.filter(tenant_id=self.request.user.tenant_id)

    def perform_create(self, serializer: serializers.BaseSerializer) -> None:
        serializer.save(
            tenant_id=self.request.user.tenant_id,
            uploaded_by_id=self.request.user.id,
        )

    @action(detail=False, methods=["post"])
    def upload(self, request: Request) -> Response:
        """Upload a file directly to S3/R2."""
        file = request.FILES.get("file")
        if not file:
            return Response({"error": "file required"}, status=status.HTTP_400_BAD_REQUEST)

        if file.size > settings.FILE_UPLOAD_MAX_SIZE:
            return Response(
                {"error": f"File too large. Max {settings.FILE_UPLOAD_MAX_SIZE / 1024 / 1024}MB"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        ext = file.name.split(".")[-1] if "." in file.name else "bin"
        file_key = f"{request.user.tenant_id}/{uuid.uuid4()}.{ext}"

        s3 = _get_s3_client()
        s3.upload_fileobj(
            file,
            settings.AWS_STORAGE_BUCKET_NAME,
            file_key,
            ExtraArgs={"ContentType": file.content_type or "application/octet-stream"},
        )

        upload = FileUpload.objects.create(
            tenant_id=request.user.tenant_id,
            original_filename=file.name,
            file_key=file_key,
            file_size=file.size,
            mime_type=file.content_type or "",
            bucket=settings.AWS_STORAGE_BUCKET_NAME,
            entity_type=request.data.get("entity_type", ""),
            entity_id=request.data.get("entity_id"),
            uploaded_by_id=request.user.id,
        )
        return Response(FileUploadSerializer(upload).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["post"])
    def presign_upload(self, request: Request) -> Response:
        """Generate a presigned URL for direct browser upload."""
        filename = request.data.get("filename", "upload")
        content_type = request.data.get("content_type", "application/octet-stream")
        ext = filename.split(".")[-1] if "." in filename else "bin"
        file_key = f"{request.user.tenant_id}/{uuid.uuid4()}.{ext}"

        s3 = _get_s3_client()
        presigned_url = s3.generate_presigned_url(
            "put_object",
            Params={
                "Bucket": settings.AWS_STORAGE_BUCKET_NAME,
                "Key": file_key,
                "ContentType": content_type,
            },
            ExpiresIn=3600,
        )

        return Response(
            {
                "presigned_url": presigned_url,
                "file_key": file_key,
                "bucket": settings.AWS_STORAGE_BUCKET_NAME,
            }
        )

    @action(detail=True, methods=["get"])
    def download_url(self, request: Request, pk=None) -> Response:
        """Generate a presigned download URL for a file."""
        upload = self.get_object()
        s3 = _get_s3_client()
        url = s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": upload.bucket, "Key": upload.file_key},
            ExpiresIn=3600,
        )
        return Response({"url": url, "filename": upload.original_filename})

    @action(detail=True, methods=["post"])
    def associate(self, request: Request, pk=None) -> Response:
        """Associate a file with an entity type/id."""
        upload = self.get_object()
        upload.entity_type = request.data.get("entity_type", upload.entity_type)
        upload.entity_id = request.data.get("entity_id", upload.entity_id)
        upload.save()
        return Response(FileUploadSerializer(upload).data)
