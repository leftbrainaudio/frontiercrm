"""Aggregation views for the Reports & Analytics system.

Implements GET /api/reports/dashboard/ and GET /api/reports/stale-deals/
per ADR-007. All metrics are computed from existing models (Deal, Activity,
TaskItem) using Django ORM aggregation — no new database tables required.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone as dt_timezone
from decimal import Decimal

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
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
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
    pipeline_id = request.query_params.get("pipeline_id")
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
        "avg_days_to_close": round(float(avg_days_agg.get("avg_days", 0) or 0) / 86400, 1),
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
            "avg_days": round(v["avg_days"], 1),
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

    permission_classes = [IsAuthenticated]

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


class StaleDealsView(APIView):
    """Returns deals that need attention — stalled, no activity, past expected close date.

    GET /api/reports/stale-deals/
      ?days_since_activity=14
      &past_close_date=true
      &limit=20
    """

    permission_classes = [IsAuthenticated]

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