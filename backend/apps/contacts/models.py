"""Contact and Account models."""

from __future__ import annotations

from django.db import models

from apps.core.models import TenantScopedModel


class Account(TenantScopedModel):
    """Company or organization account."""

    name = models.CharField(max_length=255)
    domain = models.CharField(max_length=255, blank=True, default="")
    industry = models.CharField(max_length=100, blank=True, default="")
    description = models.TextField(blank=True, default="")
    website = models.URLField(max_length=500, blank=True, default="")
    phone = models.CharField(max_length=30, blank=True, default="")
    address_line1 = models.CharField(max_length=255, blank=True, default="")
    address_line2 = models.CharField(max_length=255, blank=True, default="")
    city = models.CharField(max_length=100, blank=True, default="")
    state = models.CharField(max_length=100, blank=True, default="")
    postal_code = models.CharField(max_length=20, blank=True, default="")
    country = models.CharField(max_length=100, blank=True, default="")
    employees_count = models.IntegerField(null=True, blank=True)
    annual_revenue = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    logo_url = models.URLField(max_length=500, blank=True, default="")
    owner_id = models.UUIDField(null=True, blank=True, db_index=True)
    tags = models.JSONField(default=list, blank=True)
    custom_fields = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "contacts_account"
        indexes = [
            models.Index(fields=["tenant_id", "name"]),
            models.Index(fields=["tenant_id", "domain"]),
            models.Index(fields=["tenant_id", "industry"]),
        ]
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.name


class Contact(TenantScopedModel):
    """Individual person contact."""

    account = models.ForeignKey(
        Account,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="contacts",
    )
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(max_length=255, blank=True, default="")
    phone = models.CharField(max_length=30, blank=True, default="")
    mobile = models.CharField(max_length=30, blank=True, default="")
    job_title = models.CharField(max_length=200, blank=True, default="")
    department = models.CharField(max_length=100, blank=True, default="")
    avatar_url = models.URLField(max_length=500, blank=True, default="")
    linkedin_url = models.URLField(max_length=500, blank=True, default="")
    twitter_handle = models.CharField(max_length=100, blank=True, default="")
    street = models.CharField(max_length=255, blank=True, default="")
    city = models.CharField(max_length=100, blank=True, default="")
    state = models.CharField(max_length=100, blank=True, default="")
    postal_code = models.CharField(max_length=20, blank=True, default="")
    country = models.CharField(max_length=100, blank=True, default="")
    owner_id = models.UUIDField(null=True, blank=True, db_index=True)
    source = models.CharField(max_length=50, blank=True, default="")  # referral, website, import, api
    tags = models.JSONField(default=list, blank=True)
    custom_fields = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "contacts_contact"
        indexes = [
            models.Index(fields=["tenant_id", "email"]),
            models.Index(fields=["tenant_id", "last_name", "first_name"]),
            models.Index(fields=["tenant_id", "owner_id"]),
            models.Index(fields=["tenant_id", "-created_at"]),
        ]
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.first_name} {self.last_name}".strip() or self.email

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()
