"""Aggregation views for the Reports & Analytics system.

Implements GET /api/reports/dashboard/ and GET /api/reports/stale-deals/
per ADR-007. All metrics are computed from existing models (Deal, Activity,
TaskItem) using Django ORM aggregation — no new database tables required.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone as dt_timezone
from decimal import Decimal
from uuid import UUID as _UUID

from django.db.models import (
    Case,
    Count,
    DurationField,
    ExpressionWrapper,
    F,
    FloatField,
    IntegerField,
    OuterRef,
    Q,
    Subquery,
    Sum,
    Value,
    When,
)
from django.db.models.functions import Coalesce, TruncDate
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from apps.core.permissions import RolePermission, TenantAwarePermission
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.activities.models import Activity
from apps.pipelines.models import Deal, Stage
from apps.tasks.models import TaskItem

# ── Helpers ──────────────────────────────────────────────────────────────


def _parse_date_params(request):
    """Extract and validate start_date / end_date / pipeline_id / group_by from query params."""
    today = timezone.now().date()
    start_date_str = request.query_params.get("start_date")
    end_date_str = request.query_params.get("end_date")
    pipeline_id_str = request.query_params.get("pipeline_id")
    group_by = request.query_params.get("group_by")

    try:
        start_date = (
            date.fromisoformat(start_date_str) if start_date_str else today - timedelta(days=30)
        )
        end_date = date.fromisoformat(end_date_str) if end_date_str else today
    except (ValueError, TypeError):
        start_date = today - timedelta(days=30)
        end_date = today

    if start_date > end_date:
        start_date, end_date = end_date, start_date

    # Validate pipeline_id is a valid UUID or None
    pipeline_id = pipeline_id_str
    if pipeline_id_str:
        try:
            _UUID(pipeline_id_str)
        except (ValueError, TypeError, AttributeError):
            pipeline_id = None

    period_label = _period_label(start_date, end_date, today)
    return start_date, end_date, pipeline_id, group_by, period_label


def _period_label(start, end, today):
    """Generate a human label for the date range."""
    delta = (end - start).days
    if delta <= 1:
        return "Today"
    if delta <= 7:
        return "Last 7 days"
    if delta <= 30:
        return "Last 30 days"
    if delta <= 60:
        return "Last 60 days"
    if delta <= 90:
        return "Last 90 days"
    if delta <= 180:
        return "Last 6 months"
    if delta <= 365:
        return "Last 12 months"
    return f"{start} – {end}"


def _previous_period_range(start_date, end_date):
    """Return the date range for the previous period of equal length."""
    delta = end_date - start_date
    prev_end = start_date - timedelta(days=1)
    prev_start = prev_end - delta
    return prev_start, prev_end


def _filter_deals_queryset(qs, tenant_id, start_date, end_date, pipeline_id):
    """Apply common filters to a Deal queryset (tenant, pipeline, date)."""
    from django.db.models import Q as Q_

    filters = Q_(tenant_id=tenant_id)
    if pipeline_id:
        filters &= Q_(pipeline_id=pipeline_id)
    # Scope deals relevant to the period: created during period, or still open during period
    filters &= Q_(created_at__date__lte=end_date) & (
        Q_(status="open") | Q_(closed_at__date__gte=start_date)
    )
    return qs.filter(filters)


def _duration_to_days(value):
    """Convert backend-agnostic duration value to days.

    Django's DurationField aggregations return microseconds on PostgreSQL
    and seconds on SQLite.  This helper detects the unit by magnitude and
    normalises to days so callers never need to know the backend.
    """
    if value is None:
        return 0.0
    value = float(value)
    # PostgreSQL microseconds ≈ 8.64e10/day, SQLite seconds ≈ 86400/day
    if abs(value) > 1_000_000_000:   # past the 1e9 boundary → microseconds
        return value / 86_400_000_000
    return value / 86_400


def _compute_summary(deals_qs, prev_deals_qs):
    """Compute summary metrics for the current and previous period."""
    from django.db.models import Case, IntegerField, Sum, Value, When
    from django.db.models.functions import Coalesce

    from django.db.models import ExpressionWrapper, FloatField

    agg = deals_qs.aggregate(
        total_pipeline_value=Coalesce(
            Sum("value", filter=Q(status="open")), Value(Decimal("0.00"))
        ),
        won_value=Coalesce(Sum("value", filter=Q(status="won")), Value(Decimal("0.00"))),
        lost_value=Coalesce(Sum("value", filter=Q(status="lost")), Value(Decimal("0.00"))),
        active_deals=Count("id", filter=Q(status="open")),
        won_count=Count("id", filter=Q(status="won")),
        lost_count=Count("id", filter=Q(status="lost")),
        avg_deal_value=Coalesce(
            ExpressionWrapper(
                Sum("value") / Count("id"),
                output_field=FloatField(),
            ),
            Value(0.0, output_field=FloatField()),
        ),
        total_value=Sum("value"),
        total_count=Count("id"),
    )

    prev_agg = prev_deals_qs.aggregate(
        prev_pipeline_value=Coalesce(
            Sum("value", filter=Q(status="open")), Value(Decimal("0.00"))
        ),
        prev_won_value=Coalesce(Sum("value", filter=Q(status="won")), Value(Decimal("0.00"))),
        prev_active_deals=Count("id", filter=Q(status="open")),
        prev_won_count=Count("id", filter=Q(status="won")),
        prev_lost_count=Count("id", filter=Q(status="lost")),
        prev_avg_deal_value=Coalesce(
            ExpressionWrapper(
                Sum("value") / Count("id"),
                output_field=FloatField(),
            ),
            Value(0.0, output_field=FloatField()),
        ),
    )

    total_closed = (
        (agg["won_count"] or 0) + (agg["lost_count"] or 0)
    )
    prev_total_closed = (
        (prev_agg["prev_won_count"] or 0) + (prev_agg["prev_lost_count"] or 0)
    )

    def pct_change(current, previous):
        if previous and previous > 0:
            return float(((current - previous) / previous) * 100)
        return None

    def pp_change(current, previous):
        """Percentage-point change for win rate."""
        if current is not None and previous is not None:
            return round((current - previous) * 100, 1)
        return None

    win_rate = (agg["won_count"] / total_closed) if total_closed > 0 else 0.0
    prev_win_rate = (
        (prev_agg["prev_won_count"] / prev_total_closed) if prev_total_closed > 0 else 0.0
    )

    # Avg days to close for deals closed in period
    closed_deals = deals_qs.filter(closed_at__isnull=False)
    avg_days_agg = closed_deals.aggregate(
        avg_days=Coalesce(
            ExpressionWrapper(
                Sum(
                    ExpressionWrapper(
                        F("closed_at") - F("created_at"),
                        output_field=DurationField(),
                    )
                ) / Count("id"),
                output_field=FloatField(),
            ),
            Value(0.0, output_field=FloatField()),
        )
    )

    # Weighted pipeline = sum of deal.value * stage.probability for open deals
    weighted_qs = deals_qs.filter(status="open").annotate(
        deal_weight=ExpressionWrapper(
            F("value") * F("stage__probability"),
            output_field=FloatField(),
        )
    )
    weighted_agg = weighted_qs.aggregate(
        weighted=Coalesce(Sum("deal_weight"), Value(0.0, output_field=FloatField()))
    )

    return {
        "total_pipeline_value": float(agg["total_pipeline_value"]),
        "pipeline_value_change": pct_change(
            float(agg["total_pipeline_value"]), float(prev_agg["prev_pipeline_value"])
        ),
        "won_value": float(agg["won_value"]),
        "won_value_change": pct_change(
            float(agg["won_value"]), float(prev_agg["prev_won_value"])
        ),
        "lost_value": float(agg["lost_value"]),
        "win_rate": round(win_rate, 4),
        "win_rate_change": pp_change(win_rate, prev_win_rate),
        "active_deals": agg["active_deals"] or 0,
        "active_deals_change": (agg["active_deals"] or 0) - (prev_agg["prev_active_deals"] or 0)
        if prev_agg["prev_active_deals"] is not None
        else None,
        "avg_deal_value": float(agg["avg_deal_value"] or 0),
        "avg_deal_value_change": pct_change(
            float(agg["avg_deal_value"] or 0), float(prev_agg["prev_avg_deal_value"] or 0)
        ),
        "avg_days_to_close": round(_duration_to_days(avg_days_agg.get("avg_days", 0)), 1),
        "weighted_pipeline": float(weighted_agg.get("weighted") or 0),
    }


def _compute_pipeline_value_trend(qs, start_date, end_date):
    """Daily pipeline value (open deals) for each day in the range."""
    from django.db.models import Q as Q_

    days = []
    current = start_date
    while current <= end_date:
        day_end = datetime.combine(current, datetime.max.time()).replace(tzinfo=dt_timezone.utc)
        # Deals that were open at the end of this day
        open_on_day = qs.filter(
            Q_(created_at__date__lte=current),
            Q_(status="open") | Q_(closed_at__gt=day_end),
        )
        total = open_on_day.aggregate(
            v=Coalesce(Sum("value"), Value(Decimal("0.00")))
        )["v"]
        days.append({"date": current.isoformat(), "value": float(total)})
        current += timedelta(days=1)
    return days


def _compute_deals_by_stage(qs):
    """Group deals by stage with count, value, and probability."""
    rows = (
        qs.values(stage_name=F("stage__name"), stage_uuid=F("stage__id"), stage_probability=F("stage__probability"))
        .annotate(
            count=Count("id"),
            value=Coalesce(Sum("value"), Value(Decimal("0.00"))),
        )
        .order_by("stage__display_order")
    )
    return [
        {
            "stage_name": r["stage_name"],
            "stage_id": str(r["stage_uuid"]),
            "count": r["count"],
            "value": float(r["value"]),
            "probability": float(r["stage_probability"]),
        }
        for r in rows
    ]


def _compute_win_rate_by_stage(tenant_id, start_date, end_date, pipeline_id):
    """Compute conversion rates between consecutive stages.

    Uses Activity deal_stage_change entries to understand how many deals
    moved from one stage to the next within the period.
    """
    from django.db.models import Q as Q_

    stages = Stage.objects.filter(pipeline__tenant_id=tenant_id).order_by("display_order")
    if pipeline_id:
        stages = stages.filter(pipeline_id=pipeline_id)

    stage_list = list(stages)
    results = []
    for i in range(len(stage_list) - 1):
        from_stage = stage_list[i]
        to_stage = stage_list[i + 1]
        # Count deals that entered from_stage
        entered_count = Deal.objects.filter(
            tenant_id=tenant_id,
            stage=from_stage,
            entered_stage_at__date__gte=start_date,
            entered_stage_at__date__lte=end_date,
        )
        if pipeline_id:
            entered_count = entered_count.filter(pipeline_id=pipeline_id)
        entered = entered_count.count()

        # Count deals that advanced from from_stage to to_stage
        converted = Activity.objects.filter(
            tenant_id=tenant_id,
            activity_type="deal_stage_change",
            created_at__date__gte=start_date,
            created_at__date__lte=end_date,
            metadata__new_stage=to_stage.name,
        )

        results.append(
            {
                "from_stage": from_stage.name,
                "to_stage": to_stage.name,
                "conversion_rate": round(entered / converted, 4) if converted and entered > 0 else 0,
                "deals_entered": entered,
                "deals_converted": converted,
            }
        )
    return results


def _compute_deal_velocity(qs):
    """Compute average days in each stage for deals still in that stage."""
    from django.db.models import ExpressionWrapper, F, DurationField, Value
    from django.db.models.functions import Coalesce, Now

    velocities = (
        qs.filter(status="open")
        .values(stage_name=F("stage__name"))
        .annotate(
            deals_in_stage=Count("id"),
            avg_days=Coalesce(
                ExpressionWrapper(
                    Sum(
                        ExpressionWrapper(
                            Now() - F("entered_stage_at"),
                            output_field=DurationField(),
                        )
                    ) / Count("id"),
                    output_field=FloatField(),
                ),
                Value(0.0, output_field=FloatField()),
            ),
        )
        .order_by("stage__display_order")
    )
    return [
        {
            "stage_name": v["stage_name"],
            "avg_days": round(_duration_to_days(v["avg_days"]), 1),
            "deals_in_stage": v["deals_in_stage"],
        }
        for v in velocities
    ]


def _compute_activity_metrics(tenant_id, start_date, end_date, pipeline_id=None):
    """Aggregate activity counts by type, by day, and call duration info."""
    qs = Activity.objects.filter(
        tenant_id=tenant_id,
        created_at__date__gte=start_date,
        created_at__date__lte=end_date,
    )

    total = qs.count()

    by_type = (
        qs.values(act_type=F("activity_type"))
        .annotate(count=Count("id"))
        .order_by("-count")
    )

    activity_labels = {
        "note": "Notes",
        "call": "Calls",
        "email": "Emails",
        "meeting": "Meetings",
        "task": "Tasks",
        "deal_stage_change": "Stage Changes",
        "deal_status_change": "Status Changes",
        "file_upload": "File Uploads",
        "system": "System",
    }

    by_day_rows = (
        qs.annotate(date=TruncDate("created_at"))
        .values("date")
        .annotate(count=Count("id"))
        .order_by("date")
    )

    # Ensure all days in range are present
    day_map = {}
    current = start_date
    while current <= end_date:
        day_map[current.isoformat()] = 0
        current += timedelta(days=1)
    for row in by_day_rows:
        key = row["date"].isoformat() if row["date"] else start_date.isoformat()
        day_map[key] = row["count"]

    calls = qs.filter(activity_type="call", duration_minutes__isnull=False)
    calls_agg = calls.aggregate(
        total_minutes=Coalesce(Sum("duration_minutes"), Value(0)),
        count=Count("id"),
    )

    return {
        "total": total,
        "by_type": [
            {
                "activity_type": r["act_type"],
                "label": activity_labels.get(r["act_type"], r["act_type"].replace("_", " ").title()),
                "count": r["count"],
            }
            for r in by_type
        ],
        "by_day": [{"date": d, "count": c} for d, c in sorted(day_map.items())],
        "calls_with_duration": {
            "total_minutes": calls_agg["total_minutes"] or 0,
            "avg_minutes": round((calls_agg["total_minutes"] or 0) / calls_agg["count"], 1)
            if calls_agg["count"] > 0
            else 0,
        },
    }


def _compute_tasks_summary(tenant_id, start_date, end_date):
    """Aggregate task metrics for the reporting period."""
    now = timezone.now()
    today = now.date()

    qs = TaskItem.objects.filter(
        tenant_id=tenant_id,
    )

    total_due = qs.filter(due_at__isnull=False).count()
    overdue = qs.filter(due_at__lt=now, status__in=["todo", "in_progress"]).count()
    due_today = qs.filter(
        due_at__date=today, status__in=["todo", "in_progress"]
    ).count()

    by_priority = {}
    for label in ["urgent", "high", "medium", "low"]:
        by_priority[label] = qs.filter(priority=label, status__in=["todo", "in_progress"]).count()

    return {
        "total_due": total_due,
        "overdue": overdue,
        "due_today": due_today,
        "by_priority": by_priority,
    }


def _compute_by_owner(qs, tenant_id, start_date, end_date):
    """Break down metrics by deal owner — only included when group_by=owner."""
    from django.contrib.auth import get_user_model

    User = get_user_model()

    owners_data = (
        qs.values(deal_owner_id=F("owner_id"))
        .annotate(
            pipeline_value=Coalesce(Sum("value", filter=Q(status="open")), Value(Decimal("0.00"))),
            won_value=Coalesce(Sum("value", filter=Q(status="won")), Value(Decimal("0.00"))),
            active_deals=Count("id", filter=Q(status="open")),
            won_deals=Count("id", filter=Q(status="won")),
            lost_deals=Count("id", filter=Q(status="lost")),
            avg_deal_value=Coalesce(
                ExpressionWrapper(
                    Sum("value") / Count("id"),
                    output_field=FloatField(),
                ),
                Value(0.0, output_field=FloatField()),
            ),
        )
        .order_by("-pipeline_value")
    )

    # Activity counts per owner
    activity_by_owner = (
        Activity.objects.filter(
            tenant_id=tenant_id,
            created_at__date__gte=start_date,
            created_at__date__lte=end_date,
            actor_id__isnull=False,
        )
        .values("actor_id")
        .annotate(count=Count("id"))
    )
    activity_map = {str(r["actor_id"]): r["count"] for r in activity_by_owner}

    # Resolve owner names
    owner_ids = [str(r["deal_owner_id"]) for r in owners_data if r["deal_owner_id"]]
    users = User.objects.filter(id__in=owner_ids).values("id", "first_name", "last_name")
    user_map = {
        str(u["id"]): f"{u['first_name']} {u['last_name']}".strip() or "Unknown"
        for u in users
    }

    results = []
    for r in owners_data:
        oid = str(r["deal_owner_id"]) if r["deal_owner_id"] else ""
        total_closed = (r["won_deals"] or 0) + (r["lost_deals"] or 0)
        win_rate = round(r["won_deals"] / total_closed, 4) if total_closed > 0 else 0.0
        results.append(
            {
                "owner_id": oid,
                "owner_name": user_map.get(oid, "Unassigned"),
                "pipeline_value": float(r["pipeline_value"]),
                "won_value": float(r["won_value"]),
                "win_rate": win_rate,
                "active_deals": r["active_deals"] or 0,
                "won_deals": r["won_deals"] or 0,
                "lost_deals": r["lost_deals"] or 0,
                "avg_deal_value": float(r["avg_deal_value"] or 0),
                "activity_count": activity_map.get(oid, 0),
            }
        )
    return results


# ── Views ──────────────────────────────────────────────────────────────────


class DashboardReportView(APIView):
    """Aggregation endpoint returning all dashboard metrics in one request.

    GET /api/reports/dashboard/
      ?start_date=2026-06-01
      &end_date=2026-06-29
      &pipeline_id=<uuid>
      &group_by=owner
    """

    permission_classes = [TenantAwarePermission, RolePermission]
    required_permission = 'reports.view'

    def get(self, request):
        tenant_id = request.user.tenant_id
        start_date, end_date, pipeline_id, group_by, period_label = _parse_date_params(request)
        prev_start, prev_end = _previous_period_range(start_date, end_date)

        # Base querysets
        deals_qs = _filter_deals_queryset(
            Deal.objects.select_related("stage", "pipeline").all(),
            tenant_id,
            start_date,
            end_date,
            pipeline_id,
        )
        prev_deals_qs = _filter_deals_queryset(
            Deal.objects.all(), tenant_id, prev_start, prev_end, pipeline_id
        )

        # Compute all metrics
        summary = _compute_summary(deals_qs, prev_deals_qs)
        pipeline_value_trend = _compute_pipeline_value_trend(deals_qs, start_date, end_date)
        deals_by_stage = _compute_deals_by_stage(deals_qs)
        win_rate_by_stage = _compute_win_rate_by_stage(
            tenant_id, start_date, end_date, pipeline_id
        )
        deal_velocity = _compute_deal_velocity(deals_qs)
        activity_metrics = _compute_activity_metrics(
            tenant_id, start_date, end_date, pipeline_id
        )
        tasks_summary = _compute_tasks_summary(tenant_id, start_date, end_date)

        result = {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "label": period_label,
            },
            "summary": summary,
            "pipeline_value_trend": pipeline_value_trend,
            "deals_by_stage": deals_by_stage,
            "win_rate_by_stage": win_rate_by_stage,
            "deal_velocity": deal_velocity,
            "activity_metrics": activity_metrics,
            "tasks_summary": tasks_summary,
        }

        if group_by == "owner":
            result["by_owner"] = _compute_by_owner(deals_qs, tenant_id, start_date, end_date)

        return Response(result)


# ── Forecasting helpers ────────────────────────────────────────────────────


def _parse_quarter(quarter_str: str | None) -> tuple[date, date]:
    """Convert a quarter string (e.g. "2026-Q3", "current") to (start_date, end_date)."""
    today = timezone.now().date()
    if not quarter_str or quarter_str == "current":
        quarter_str = f"{today.year}-Q{(today.month - 1) // 3 + 1}"

    try:
        year_str, q_str = quarter_str.split("-Q")
        year = int(year_str)
        q = int(q_str)
    except (ValueError, IndexError):
        # Fall back to current quarter
        q = (today.month - 1) // 3 + 1
        year = today.year

    start_month = 3 * (q - 1) + 1
    end_month = 3 * q

    start_date = date(year, start_month, 1)

    if end_month == 12:
        end_date = date(year, 12, 31)
    else:
        end_date = date(year, end_month + 1, 1) - timedelta(days=1)

    return start_date, end_date


def _compute_simple_weighted_forecast(deals_qs):
    """Simple weighted projection: Σ(open_deal.value × stage.probability).

    Reuses the same logic as _compute_summary's weighted_pipeline.
    Returns projected revenue, deal count, and total pipeline value.
    """
    open_deals = deals_qs.filter(status="open")
    total_pipeline = open_deals.aggregate(
        total=Coalesce(Sum("value"), Value(Decimal("0.00")))
    )["total"]

    weighted_qs = open_deals.annotate(
        deal_weight=ExpressionWrapper(
            F("value") * F("stage__probability"),
            output_field=FloatField(),
        )
    )
    weighted_agg = weighted_qs.aggregate(
        projected=Coalesce(Sum("deal_weight"), Value(0.0, output_field=FloatField()))
    )

    return {
        "projected_revenue": round(float(weighted_agg["projected"]), 2),
        "deals_in_pipeline": open_deals.count(),
        "total_pipeline_value": float(total_pipeline),
        "description": "Sum of deal.value × stage.probability for all open deals",
    }


def _compute_win_rate_adjusted(weighted_value: float, tenant_id: str, start_date: date, end_date: date) -> dict:
    """Win-rate adjusted projection: weighted_pipeline × historical_win_rate.

    Historical win rate = won / (won + lost) across all deals in the last 12 months.
    """
    twelve_months_ago = start_date - timedelta(days=365)

    closed_deals = Deal.objects.filter(
        tenant_id=tenant_id,
        status__in=["won", "lost"],
        closed_at__date__gte=twelve_months_ago,
        closed_at__date__lte=end_date,
    )
    closed_agg = closed_deals.aggregate(
        won_count=Count("id", filter=Q(status="won")),
        lost_count=Count("id", filter=Q(status="lost")),
    )
    won = closed_agg["won_count"] or 0
    lost = closed_agg["lost_count"] or 0
    total_closed = won + lost
    historical_win_rate = round(won / total_closed, 4) if total_closed > 0 else 0.0

    return {
        "projected_revenue": round(float(weighted_value) * historical_win_rate, 2),
        "historical_win_rate": historical_win_rate,
        "adjustment_factor": historical_win_rate,
        "description": "Weighted pipeline × historical win rate",
    }


def _compute_velocity_forecast(deals_qs, tenant_id) -> dict:
    """Velocity-based projection with monthly breakdown.

    For each open deal, estimate the close date using expected_close_date or
    entered_stage_at + avg_days_in_stage from deal_velocity data.
    Group by month and sum projected values.
    """
    from decimal import Decimal

    open_deals = list(
        deals_qs.filter(status="open").select_related("stage")
    )

    # Build stage velocity map: stage_name → avg_days
    velocity_data = _compute_deal_velocity(
        Deal.objects.filter(tenant_id=tenant_id)
    )
    stage_velocity = {v["stage_name"]: v["avg_days"] for v in velocity_data}

    now = timezone.now()
    monthly: dict[str, dict] = {}
    deals_with_dates = 0
    total_projected = Decimal("0.00")
    total_expected_close_count = 0

    for deal in open_deals:
        # Effective projection = deal.value × win_probability
        projected_value = deal.value * deal.win_probability

        # Estimate close date
        est_close = deal.expected_close_date
        if est_close is None and deal.entered_stage_at:
            # Use velocity: entered_stage_at + avg_days_in_stage
            avg_days = stage_velocity.get(deal.stage.name, 45)
            est_close = (deal.entered_stage_at + timedelta(days=int(avg_days))).date()

        if est_close is not None:
            deals_with_dates += 1
            if est_close >= now.date():
                total_expected_close_count += 1

            month_key = est_close.strftime("%Y-%m")
            if month_key not in monthly:
                monthly[month_key] = {"projected_value": Decimal("0.00"), "expected_deals": 0}
            monthly[month_key]["projected_value"] += projected_value
            monthly[month_key]["expected_deals"] += 1

        total_projected += projected_value

    # Determine quarter boundaries from the deals (use earliest relevant month)
    if monthly:
        months_sorted = sorted(monthly.keys())
        avg_days_list = [v["avg_days"] for v in velocity_data if v["avg_days"] > 0]
        avg_days_to_close = round(
            sum(avg_days_list) / len(avg_days_list), 1
        ) if avg_days_list else 0.0
    else:
        avg_days_to_close = 0.0

    monthly_breakdown = [
        {
            "month": m,
            "projected_value": round(float(v["projected_value"]), 2),
            "expected_deals": v["expected_deals"],
        }
        for m, v in sorted(monthly.items())
    ]

    return {
        "projected_revenue": float(total_projected),
        "expected_close_count": total_expected_close_count,
        "deals_with_expected_dates": deals_with_dates,
        "avg_days_to_close": avg_days_to_close,
        "monthly_breakdown": monthly_breakdown,
    }


def _parse_forecast_range(
    quarter_str: str | None,
    range_str: str | None,
) -> tuple[str, date, date]:
    """Parse quarter and/or range params, returning (label, start, end).

    ``quarter`` takes priority (exact quarter spec like '2026-Q3').
    ``range`` is used when quarter is not provided: 'quarter' (3mo),
    'half-year' (6mo), 'year' (12mo).  Defaults to current quarter.
    """
    if quarter_str and quarter_str != "current":
        start, end = _parse_quarter(quarter_str)
        return quarter_str, start, end

    today = timezone.now().date()
    range_map = {
        "quarter": 90,
        "half-year": 180,
        "year": 365,
    }
    days = range_map.get(range_str or "quarter", 90)
    start = today
    end = today + timedelta(days=days)

    # Trim to month ends for consistent boundaries
    # start = first of current month
    start = date(today.year, today.month, 1)
    label = (
        "Next 3 Months" if days == 90
        else "Next 6 Months" if days == 180
        else "Next 12 Months"
    )
    return label, start, end


def _compute_deal_forecasts(deals_qs, tenant_id) -> list[dict]:
    """Per-deal forecast breakdown with projected close info.

    Returns a list of open deals with estimated close dates,
    probability weights, and projected revenue.
    """
    open_deals = list(
        deals_qs.filter(status="open").select_related("stage", "pipeline")
    )

    velocity_data = _compute_deal_velocity(
        Deal.objects.filter(tenant_id=tenant_id)
    )
    stage_velocity = {v["stage_name"]: v["avg_days"] for v in velocity_data}
    now = timezone.now()

    results = []
    for deal in open_deals:
        est_close = deal.expected_close_date
        if est_close is None and deal.entered_stage_at:
            avg_days = stage_velocity.get(deal.stage.name, 45)
            est_close = (deal.entered_stage_at + timedelta(days=int(avg_days))).date()

        prob_weight = float(deal.win_probability)
        projected = float(deal.value) * prob_weight

        results.append({
            "deal_id": str(deal.id),
            "deal_name": deal.name,
            "deal_value": float(deal.value),
            "stage_name": deal.stage.name if deal.stage else "",
            "stage_probability": float(deal.stage.probability) if deal.stage else 0.0,
            "probability_weight": prob_weight,
            "projected_value": round(projected, 2),
            "estimated_close_date": est_close.isoformat() if est_close else None,
            "pipeline_name": deal.pipeline.name if deal.pipeline else "",
            "has_expected_date": deal.expected_close_date is not None,
        })

    results.sort(
        key=lambda r: r["estimated_close_date"] or "9999-12-31"
    )
    return results


def _compute_what_if(deals_qs, tenant_id, scenario_stage_name: str, scenario_close_rate: float) -> dict | None:
    """What-if scenario projection.

    current_value_in_stage × (scenario_close_rate / current_stage_probability)
    Shows delta between current projection and scenario projection.
    """
    from decimal import Decimal

    stage = Stage.objects.filter(
        name__iexact=scenario_stage_name,
        pipeline__tenant_id=tenant_id,
    ).first()
    if not stage:
        return None

    stage_deals = list(deals_qs.filter(status="open", stage=stage).select_related("stage"))

    current_probability = float(stage.probability)
    total_value_in_stage = Decimal("0.00")
    current_projected = Decimal("0.00")

    for deal in stage_deals:
        total_value_in_stage += deal.value
        current_projected += deal.value * deal.win_probability

    scenario_projected = total_value_in_stage * Decimal(str(scenario_close_rate / current_probability)) if current_probability > 0 else Decimal("0.00")

    return {
        "stage_name": stage.name,
        "current_close_rate": current_probability,
        "scenario_close_rate": scenario_close_rate,
        "deals_affected": len(stage_deals),
        "current_projected_value": round(float(current_projected), 2),
        "scenario_projected_value": round(float(scenario_projected), 2),
        "upside": round(float(scenario_projected - current_projected), 2),
    }


class ForecastView(APIView):
    """Pipeline forecasting endpoint with multiple projection models.

    GET /api/reports/forecast/
      ?pipeline_id=<uuid>
      &quarter=2026-Q3
      &range=quarter|half-year|year
      &scenario_stage=Negotiation
      &scenario_close_rate=0.80
      &confidence_level=conservative|medium|optimistic
    """

    permission_classes = [TenantAwarePermission, RolePermission]
    required_permission = "forecast.view"

    def get(self, request):
        tenant_id = request.user.tenant_id
        pipeline_id = request.query_params.get("pipeline_id")
        quarter_str = request.query_params.get("quarter")
        range_str = request.query_params.get("range", "quarter")
        scenario_stage = request.query_params.get("scenario_stage")
        scenario_close_rate_str = request.query_params.get("scenario_close_rate")
        confidence_level = request.query_params.get("confidence_level", "medium")

        # Parse forecast range → date range
        period_label, start_date, end_date = _parse_forecast_range(quarter_str, range_str)

        # Validate pipeline_id
        if pipeline_id:
            try:
                _UUID(pipeline_id)
            except (ValueError, TypeError, AttributeError):
                pipeline_id = None

        # Parse scenario_close_rate
        scenario_close_rate = None
        if scenario_close_rate_str:
            try:
                scenario_close_rate = float(scenario_close_rate_str)
            except (ValueError, TypeError):
                scenario_close_rate = None

        # Base queryset — all open deals for the current pipeline scope
        deals_qs = _filter_deals_queryset(
            Deal.objects.select_related("stage", "pipeline").all(),
            tenant_id,
            start_date,
            end_date,
            pipeline_id,
        )

        # Confidence level multipliers
        confidence_multipliers = {
            "conservative": 0.8,
            "medium": 1.0,
            "optimistic": 1.15,
        }
        multiplier = confidence_multipliers.get(confidence_level, 1.0)

        # 1. Simple weighted projection
        simple = _compute_simple_weighted_forecast(deals_qs)
        simple["projected_revenue"] = round(simple["projected_revenue"] * multiplier, 2)

        # 2. Win-rate adjusted
        win_rate_adj = _compute_win_rate_adjusted(
            simple["projected_revenue"], tenant_id, start_date, end_date
        )
        win_rate_adj["projected_revenue"] = round(
            win_rate_adj["projected_revenue"] * multiplier, 2
        )

        # 3. Velocity-based
        velocity = _compute_velocity_forecast(deals_qs, tenant_id)

        # 4. What-if scenario
        what_if = None
        if scenario_stage and scenario_close_rate is not None:
            what_if = _compute_what_if(deals_qs, tenant_id, scenario_stage, scenario_close_rate)

        # 5. Per-deal breakdown
        deal_forecasts = _compute_deal_forecasts(deals_qs, tenant_id)

        return Response(
            {
                "period": {
                    "quarter": quarter_str if quarter_str else period_label,
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "label": period_label,
                },
                "projections": {
                    "simple_weighted": simple,
                    "win_rate_adjusted": win_rate_adj,
                    "velocity_based": velocity,
                },
                "scenario": {
                    "stage_name": scenario_stage,
                    "close_rate": scenario_close_rate,
                    "confidence_level": confidence_level,
                }
                if scenario_stage
                else None,
                "what_if": what_if,
                "deal_forecasts": deal_forecasts,
            }
        )


class StaleDealsView(APIView):
    """Returns deals that need attention — stalled, no activity, past expected close date.

    GET /api/reports/stale-deals/
      ?days_since_activity=14
      &past_close_date=true
      &limit=20
    """

    permission_classes = [TenantAwarePermission, RolePermission]
    required_permission = "reports.view"

    def get(self, request):
        tenant_id = request.user.tenant_id
        days_since_activity = int(
            request.query_params.get("days_since_activity", 14)
        )
        past_close_date_flag = (
            request.query_params.get("past_close_date", "true").lower() == "true"
        )
        limit = int(request.query_params.get("limit", 20))

        now = timezone.now()
        activity_threshold = now - timedelta(days=days_since_activity)

        # Only open deals
        base_qs = Deal.objects.filter(
            tenant_id=tenant_id,
            status="open",
            stage__pipeline__is_active=True,
        ).select_related("stage", "pipeline")

        # Subquery: latest activity date per deal
        latest_activity_subq = (
            Activity.objects.filter(
                tenant_id=tenant_id,
                entity_type="deal",
                entity_id=OuterRef("id"),
            )
            .order_by("-created_at")
            .values("created_at")[:1]
        )

        deals_with_activity = base_qs.annotate(
            last_activity_at=Subquery(latest_activity_subq),
        )

        # Apply filters
        filters = Q()
        if days_since_activity > 0:
            filters |= Q(last_activity_at__lt=activity_threshold) | Q(last_activity_at__isnull=True)
        if past_close_date_flag:
            filters &= Q(expected_close_date__lt=now.date())

        stale = deals_with_activity.filter(filters).order_by("expected_close_date")[:limit]

        results = []
        for deal in stale:
            last_activity = deal.last_activity_at
            if last_activity:
                days_since = (now - last_activity).days
            else:
                days_since = 9999  # No activity ever

            entered = deal.entered_stage_at or deal.created_at
            days_in_stage = (now - entered).days if entered else 0

            results.append(
                {
                    "id": str(deal.id),
                    "name": deal.name,
                    "value": float(deal.value),
                    "stage_name": deal.stage.name if deal.stage else "",
                    "owner_name": "",
                    "days_in_stage": days_in_stage,
                    "days_since_last_activity": days_since,
                    "expected_close_date": (
                        deal.expected_close_date.isoformat()
                        if deal.expected_close_date
                        else None
                    ),
                    "is_overdue": (
                        deal.expected_close_date < now.date()
                        if deal.expected_close_date
                        else False
                    ),
                }
            )

        # Resolve owner names
        owner_ids = [str(d.owner_id) for d in stale if d.owner_id]
        if owner_ids:
            from django.contrib.auth import get_user_model

            User = get_user_model()
            users = User.objects.filter(id__in=owner_ids).values("id", "first_name", "last_name")
            user_map = {
                str(u["id"]): f"{u['first_name']} {u['last_name']}".strip() or "Unknown"
                for u in users
            }
            for r in results:
                owner_uuid = None
                for d in stale:
                    if str(d.id) == r["id"]:
                        owner_uuid = str(d.owner_id) if d.owner_id else None
                        break
                r["owner_name"] = user_map.get(owner_uuid, "Unassigned")

        return Response({"stale_deals": results})


class ReportExportView(APIView):
    """Export report data as CSV or printable HTML.

    GET /api/reports/export/csv/  — key-value CSV of dashboard metrics
    GET /api/reports/export/html/ — printable HTML page of report data
    """

    permission_classes = [TenantAwarePermission, RolePermission]
    required_permission = "reports.export"

    def _get_report_data(self, request):
        """Reuse dashboard computation to generate report data."""
        tenant_id = request.user.tenant_id
        start_date, end_date, pipeline_id, group_by, period_label = _parse_date_params(request)
        prev_start, prev_end = _previous_period_range(start_date, end_date)

        deals_qs = _filter_deals_queryset(
            Deal.objects.select_related("stage", "pipeline").all(),
            tenant_id, start_date, end_date, pipeline_id,
        )
        prev_deals_qs = _filter_deals_queryset(
            Deal.objects.all(), tenant_id, prev_start, prev_end, pipeline_id,
        )

        return {
            "period": {"start_date": start_date.isoformat(), "end_date": end_date.isoformat(), "label": period_label},
            "summary": _compute_summary(deals_qs, prev_deals_qs),
            "deals_by_stage": _compute_deals_by_stage(deals_qs),
            "deal_velocity": _compute_deal_velocity(deals_qs),
            "activity_metrics": _compute_activity_metrics(tenant_id, start_date, end_date, pipeline_id),
            "tasks_summary": _compute_tasks_summary(tenant_id, start_date, end_date),
        }

    def get(self, request):
        export_format = request.resolver_match.url_name
        if export_format == "reports-export-csv":
            return self._export_csv(request)
        return self._export_html(request)

    def _export_csv(self, request):
        """Flatten report data into key-value CSV rows."""
        from django.http import StreamingHttpResponse

        data = self._get_report_data(request)

        def stream():
            import csv, io
            buf = io.StringIO()
            writer = csv.writer(buf)

            # Section: Summary
            writer.writerow(["Section", "Metric", "Value"])
            summary = data["summary"]
            for key, val in summary.items():
                writer.writerow(["Summary", key.replace("_", " ").title(), str(val)])

            # Section: Deals by stage
            for s in data.get("deals_by_stage", []):
                writer.writerow(["Deals by Stage", s["stage_name"], f"Count: {s['count']}, Value: {s['value']}"])

            # Section: Deal velocity
            for v in data.get("deal_velocity", []):
                writer.writerow(["Deal Velocity", v["stage_name"], f"Avg days: {v['avg_days']}, Deals: {v['deals_in_stage']}"])

            # Section: Activity
            am = data.get("activity_metrics", {})
            writer.writerow(["Activity", "Total", str(am.get("total", 0))])
            for t in am.get("by_type", []):
                writer.writerow(["Activity by Type", t["label"], str(t["count"])])

            # Section: Tasks
            ts = data.get("tasks_summary", {})
            writer.writerow(["Tasks", "Total Due", str(ts.get("total_due", 0))])
            writer.writerow(["Tasks", "Overdue", str(ts.get("overdue", 0))])

            buf.seek(0)
            yield buf.read()

        response = StreamingHttpResponse(stream(), content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="report.csv"'
        return response

    def _export_html(self, request):
        """Generate a printable HTML page of report data."""
        data = self._get_report_data(request)
        summary = data["summary"]
        period = data["period"]

        def _fmt(v):
            if isinstance(v, float):
                if abs(v) >= 1_000_000:
                    return f"${v:,.2f}"
                if abs(v) >= 1_000:
                    return f"${v:,.0f}"
                return f"{v:,.2f}"
            return str(v)

        deals_stage_rows = "".join(
            f"<tr><td>{s['stage_name']}</td><td>{s['count']}</td><td>{_fmt(s['value'])}</td></tr>"
            for s in data.get("deals_by_stage", [])
        )
        velocity_rows = "".join(
            f"<tr><td>{v['stage_name']}</td><td>{v['avg_days']}</td><td>{v['deals_in_stage']}</td></tr>"
            for v in data.get("deal_velocity", [])
        )
        activity_rows = "".join(
            f"<tr><td>{t['label']}</td><td>{t['count']}</td></tr>"
            for t in data.get("activity_metrics", {}).get("by_type", [])
        )

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>FrontierCRM Report — {period['label']}</title>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 40px; color: #111; }}
  h1 {{ font-size: 24px; margin-bottom: 4px; }}
  h2 {{ font-size: 18px; margin-top: 32px; border-bottom: 1px solid #ddd; padding-bottom: 6px; }}
  .period {{ color: #666; font-size: 14px; margin-bottom: 24px; }}
  table {{ border-collapse: collapse; width: 100%; margin: 12px 0; }}
  th, td {{ text-align: left; padding: 8px 12px; border-bottom: 1px solid #eee; font-size: 14px; }}
  th {{ background: #f5f5f5; font-weight: 600; }}
  .summary-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 16px; margin: 16px 0; }}
  .summary-card {{ background: #f9f9f9; border-radius: 8px; padding: 16px; }}
  .summary-card .label {{ font-size: 12px; color: #666; text-transform: uppercase; letter-spacing: 0.5px; }}
  .summary-card .value {{ font-size: 22px; font-weight: 700; margin-top: 4px; }}
  @media print {{ body {{ margin: 20px; }} .no-print {{ display: none; }} }}
</style>
</head>
<body>
<h1>FrontierCRM Report</h1>
<p class="period">{period['label']} ({period['start_date']} – {period['end_date']})</p>

<div class="summary-grid">
  <div class="summary-card"><div class="label">Pipeline Value</div><div class="value">{_fmt(summary['total_pipeline_value'])}</div></div>
  <div class="summary-card"><div class="label">Won Value</div><div class="value">{_fmt(summary['won_value'])}</div></div>
  <div class="summary-card"><div class="label">Win Rate</div><div class="value">{summary['win_rate']*100:.1f}%</div></div>
  <div class="summary-card"><div class="label">Active Deals</div><div class="value">{summary['active_deals']}</div></div>
  <div class="summary-card"><div class="label">Avg Days to Close</div><div class="value">{summary['avg_days_to_close']}d</div></div>
  <div class="summary-card"><div class="label">Weighted Pipeline</div><div class="value">{_fmt(summary['weighted_pipeline'])}</div></div>
</div>

<h2>Deals by Stage</h2>
<table><thead><tr><th>Stage</th><th>Count</th><th>Value</th></tr></thead><tbody>{deals_stage_rows}</tbody></table>

<h2>Deal Velocity</h2>
<table><thead><tr><th>Stage</th><th>Avg Days</th><th>Deals</th></tr></thead><tbody>{velocity_rows}</tbody></table>

<h2>Activity</h2>
<table><thead><tr><th>Type</th><th>Count</th></tr></thead><tbody>{activity_rows}</tbody></table>
<p><em>Total: {data.get('activity_metrics', {}).get('total', 0)} activities</em></p>

<h2>Tasks</h2>
<table><thead><tr><th>Status</th><th>Count</th></tr></thead><tbody>
<tr><td>Total Due</td><td>{data.get('tasks_summary', {}).get('total_due', 0)}</td></tr>
<tr><td>Overdue</td><td>{data.get('tasks_summary', {}).get('overdue', 0)}</td></tr>
<tr><td>Due Today</td><td>{data.get('tasks_summary', {}).get('due_today', 0)}</td></tr>
</tbody></table>

<p class="no-print" style="margin-top: 32px; color: #888; font-size: 13px;">Generated by FrontierCRM on {__import__('datetime').datetime.now().strftime('%B %d, %Y at %H:%M')}</p>
</body>
</html>"""
        return HttpResponse(html, content_type="text/html; charset=utf-8")