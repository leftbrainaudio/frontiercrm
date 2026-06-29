"""Pipeline and Deal models."""

from __future__ import annotations

from decimal import Decimal

from django.db import models

from apps.core.models import TenantScopedModel


class Pipeline(TenantScopedModel):
    """Sales pipeline / funnel."""

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "pipelines_pipeline"
        indexes = [
            models.Index(fields=["tenant_id", "is_default"]),
            models.Index(fields=["tenant_id", "-created_at"]),
        ]
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Stage(TenantScopedModel):
    """A stage within a pipeline (e.g. 'Qualified', 'Proposal')."""

    pipeline = models.ForeignKey(
        Pipeline,
        on_delete=models.CASCADE,
        related_name="stages",
    )
    name = models.CharField(max_length=255)
    display_order = models.IntegerField(default=0)
    probability = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Win probability for deals in this stage (0.00 - 1.00)",
    )
    color = models.CharField(max_length=7, default="#6B7280", help_text="Hex color for the stage")
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "pipelines_stage"
        indexes = [
            models.Index(fields=["pipeline", "display_order"]),
        ]
        ordering = ["display_order"]

    def __str__(self) -> str:
        return f"{self.pipeline.name} / {self.name}"


class Deal(TenantScopedModel):
    """Sales deal / opportunity tracked through a pipeline."""

    class DealStatus(models.TextChoices):
        OPEN = "open", "Open"
        WON = "won", "Won"
        LOST = "lost", "Lost"
        ABANDONED = "abandoned", "Abandoned"

    name = models.CharField(max_length=255)
    pipeline = models.ForeignKey(
        Pipeline,
        on_delete=models.CASCADE,
        related_name="deals",
    )
    stage = models.ForeignKey(
        Stage,
        on_delete=models.CASCADE,
        related_name="deals",
    )
    contact = models.ForeignKey(
        "contacts.Contact",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="deals",
    )
    account = models.ForeignKey(
        "contacts.Account",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="deals",
    )
    value = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal("0.00"))
    currency = models.CharField(max_length=3, default="USD")
    status = models.CharField(max_length=20, choices=DealStatus.choices, default=DealStatus.OPEN)
    probability = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Override win probability (0.00 - 1.00). If null, uses stage probability",
    )
    expected_close_date = models.DateField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    close_reason = models.CharField(max_length=255, blank=True, default="")
    owner_id = models.UUIDField(null=True, blank=True, db_index=True)
    description = models.TextField(blank=True, default="")
    tags = models.JSONField(default=list, blank=True)
    custom_fields = models.JSONField(default=dict, blank=True)
    # Stage tracking
    entered_stage_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "pipelines_deal"
        indexes = [
            models.Index(fields=["tenant_id", "status"]),
            models.Index(fields=["tenant_id", "pipeline", "stage"]),
            models.Index(fields=["tenant_id", "owner_id"]),
            models.Index(fields=["tenant_id", "expected_close_date"]),
            models.Index(fields=["tenant_id", "-created_at"]),
        ]
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.name

    @property
    def win_probability(self) -> Decimal:
        """Effective win probability — override or stage default."""
        if self.probability is not None:
            return self.probability
        return self.stage.probability

    @property
    def weighted_value(self) -> Decimal:
        """Expected value = deal value × win probability."""
        return self.value * self.win_probability
