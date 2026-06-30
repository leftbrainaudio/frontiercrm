"""Streaming CSV export views for pipeline reports."""

from __future__ import annotations

import csv
import io
import re
from datetime import date
from decimal import Decimal

from django.http import StreamingHttpResponse
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.pipelines.models import Deal

from .views import (
    _compute_deal_forecasts,
    _compute_deal_velocity,
    _compute_deals_by_stage,
    _compute_simple_weighted_forecast,
    _compute_summary,
    _compute_velocity_forecast,
    _compute_what_if,
    _compute_win_rate_adjusted,
    _filter_deals_queryset,
    _parse_date_params,
    _parse_forecast_range,
    _previous_period_range,
)
# Regex: starts with =, +, -, or @ (after stripping leading whitespace).
# Tab (\t) is our sanitizer prefix — don't include it in the trigger set
# or we'll double-sanitize already-sanitized fields.
_FORMULA_INJECTION_RE = re.compile(r"^[\s]*[=+\-@]")


# ── Helpers ────────────────────────────────────────────────────────────


def _sanitize_csv_field(value: str | int | float | Decimal | None) -> str:
    """Prevent CSV formula injection by prefixing dangerous values.

    Fields starting with =, +, -, or @ are prepended with a tab so
    spreadsheet applications (Excel, Google Sheets, LibreOffice Calc)
    display them as text rather than interpreting them as formulas.

    Already-sanitised fields (leading tab) are returned unchanged so the
    operation is idempotent.

    Returns the sanitised string.  Non-string values are converted via str()
    before the check so numeric types are also protected.
    """
    s = str(value)
    if s.startswith("\t"):  # already sanitised — idempotent
        return s
    if _FORMULA_INJECTION_RE.match(s):
        return "\t" + s
    return s


class _SanitizingCSVWriter:
    """csv.writer wrapper that applies formula-injection sanitization to every field."""

    def __init__(self, buffer):
        self.writer = csv.writer(buffer)

    def writerow(self, row):
        self.writer.writerow([_sanitize_csv_field(v) for v in row])

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)


class PipelineReportExportView(APIView):
    """Streaming CSV export of the current pipeline report.

    GET /api/reports/export/pipeline/csv/?start_date=&end_date=&pipeline_id=
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        tenant_id = request.user.tenant_id
        start_date, end_date, pipeline_id, _group_by, _period_label = _parse_date_params(request)
        prev_start, prev_end = _previous_period_range(start_date, end_date)

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

        summary = _compute_summary(deals_qs, prev_deals_qs)
        deals_by_stage = _compute_deals_by_stage(deals_qs)
        deal_velocity = _compute_deal_velocity(deals_qs)

        headers = ["Section", "Metric", "Value"]

        def fmt_currency(val: float) -> str:
            return f"${val:,.2f}"

        def fmt_percent(val: float) -> str:
            return f"{val * 100:.2f}%"

        def stream():
            buffer = io.StringIO()
            writer = _SanitizingCSVWriter(buffer)
            writer.writerow(headers)
            yield buffer.getvalue()
            buffer.seek(0)
            buffer.truncate(0)

            # Summary section
            writer2 = _SanitizingCSVWriter(buffer)
            writer2.writerow(["Summary", "Total Pipeline Value", fmt_currency(summary["total_pipeline_value"])])
            yield buffer.getvalue()
            buffer.seek(0)
            buffer.truncate(0)
            writer2.writerow(["Summary", "Weighted Pipeline", fmt_currency(summary["weighted_pipeline"])])
            yield buffer.getvalue()
            buffer.seek(0)
            buffer.truncate(0)
            writer2.writerow(["Summary", "Won Value", fmt_currency(summary["won_value"])])
            yield buffer.getvalue()
            buffer.seek(0)
            buffer.truncate(0)
            writer2.writerow(["Summary", "Lost Value", fmt_currency(summary["lost_value"])])
            yield buffer.getvalue()
            buffer.seek(0)
            buffer.truncate(0)
            writer2.writerow(["Summary", "Win Rate", fmt_percent(summary["win_rate"])])
            yield buffer.getvalue()
            buffer.seek(0)
            buffer.truncate(0)
            writer2.writerow(["Summary", "Active Deals", str(summary["active_deals"])])
            yield buffer.getvalue()
            buffer.seek(0)
            buffer.truncate(0)
            writer2.writerow(["Summary", "Avg Deal Value", fmt_currency(summary["avg_deal_value"])])
            yield buffer.getvalue()
            buffer.seek(0)
            buffer.truncate(0)
            writer2.writerow(["Summary", "Avg Days to Close", f'{summary["avg_days_to_close"]} days'])
            yield buffer.getvalue()
            buffer.seek(0)
            buffer.truncate(0)

            # Deals by Stage section
            writer2.writerow([])  # blank separator row
            yield buffer.getvalue()
            buffer.seek(0)
            buffer.truncate(0)
            writer2.writerow(["Deals by Stage", "Stage", "Count", "Value"])
            yield buffer.getvalue()
            buffer.seek(0)
            buffer.truncate(0)
            for row in deals_by_stage:
                writer2.writerow([
                    "Deals by Stage",
                    f'{row["stage_name"]} ({row["count"]})',
                    row["count"],
                    fmt_currency(row["value"]),
                ])
                yield buffer.getvalue()
                buffer.seek(0)
                buffer.truncate(0)

            # Deal Velocity section
            writer2.writerow([])  # blank separator row
            yield buffer.getvalue()
            buffer.seek(0)
            buffer.truncate(0)
            writer2.writerow(["Deal Velocity", "Stage", "Avg Days", "Deals in Stage"])
            yield buffer.getvalue()
            buffer.seek(0)
            buffer.truncate(0)
            for v in deal_velocity:
                writer2.writerow([
                    "Deal Velocity",
                    v["stage_name"],
                    f'{v["avg_days"]} days',
                    v["deals_in_stage"],
                ])
                yield buffer.getvalue()
                buffer.seek(0)
                buffer.truncate(0)

        response = StreamingHttpResponse(
            streaming_content=stream(),
            content_type="text/csv",
        )
        filename = f"pipeline-report-{date.today().isoformat()}.csv"
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response


class ForecastExportView(APIView):
    """Streaming CSV export of the forecast data.

    GET /api/reports/export/forecast/csv/
      ?pipeline_id=<uuid>
      &range=quarter|half-year|year
      &scenario_stage=Negotiation
      &scenario_close_rate=0.80
      &confidence_level=conservative|medium|optimistic
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        tenant_id = request.user.tenant_id
        pipeline_id = request.query_params.get("pipeline_id")
        range_str = request.query_params.get("range", "quarter")
        scenario_stage = request.query_params.get("scenario_stage")
        scenario_close_rate_str = request.query_params.get("scenario_close_rate")
        confidence_level = request.query_params.get("confidence_level", "medium")

        from uuid import UUID as _UUID

        # Parse range
        period_label, start_date, end_date = _parse_forecast_range(
            request.query_params.get("quarter"), range_str
        )

        # Validate pipeline_id
        if pipeline_id:
            try:
                _UUID(pipeline_id)
            except (ValueError, TypeError, AttributeError):
                pipeline_id = None

        scenario_close_rate = None
        if scenario_close_rate_str:
            try:
                scenario_close_rate = float(scenario_close_rate_str)
            except (ValueError, TypeError):
                scenario_close_rate = None

        # Base queryset
        deals_qs = _filter_deals_queryset(
            Deal.objects.select_related("stage", "pipeline").all(),
            tenant_id, start_date, end_date, pipeline_id,
        )

        # Confidence multipliers
        confidence_multipliers = {
            "conservative": 0.8,
            "medium": 1.0,
            "optimistic": 1.15,
        }
        multiplier = confidence_multipliers.get(confidence_level, 1.0)

        # Compute projections
        simple = _compute_simple_weighted_forecast(deals_qs)
        simple["projected_revenue"] = round(simple["projected_revenue"] * multiplier, 2)

        win_rate_adj = _compute_win_rate_adjusted(
            simple["projected_revenue"], tenant_id, start_date, end_date
        )
        win_rate_adj["projected_revenue"] = round(
            win_rate_adj["projected_revenue"] * multiplier, 2
        )

        velocity = _compute_velocity_forecast(deals_qs, tenant_id)

        what_if = None
        if scenario_stage and scenario_close_rate is not None:
            what_if = _compute_what_if(deals_qs, tenant_id, scenario_stage, scenario_close_rate)

        deal_forecasts = _compute_deal_forecasts(deals_qs, tenant_id)

        def fmt_currency(val: float) -> str:
            return f"${val:,.2f}"

        def stream():
            buffer = io.StringIO()
            writer = _SanitizingCSVWriter(buffer)

            # === Summary Projections ===
            writer.writerow(["Section", "Projection Type", "Projected Revenue", "Description"])
            yield buffer.getvalue()
            buffer.seek(0)
            buffer.truncate(0)
            writer.writerow(["Summary", "Simple Weighted", fmt_currency(simple["projected_revenue"]), simple["description"]])
            yield buffer.getvalue()
            buffer.seek(0)
            buffer.truncate(0)
            writer.writerow(["Summary", "Win-Rate Adjusted", fmt_currency(win_rate_adj["projected_revenue"]), win_rate_adj["description"]])
            yield buffer.getvalue()
            buffer.seek(0)
            buffer.truncate(0)
            writer.writerow(["Summary", "Velocity Based", fmt_currency(velocity["projected_revenue"]), "Based on avg deal velocity"])
            yield buffer.getvalue()
            buffer.seek(0)
            buffer.truncate(0)
            writer.writerow(["Summary", "Expected Deals Closed", str(velocity["expected_close_count"]), f'{velocity["deals_with_expected_dates"]} deals with dates'])
            yield buffer.getvalue()
            buffer.seek(0)
            buffer.truncate(0)
            writer.writerow(["Summary", "Avg Days to Close", str(velocity["avg_days_to_close"]), ""])
            yield buffer.getvalue()
            buffer.seek(0)
            buffer.truncate(0)

            # === Monthly Breakdown ===
            if velocity.get("monthly_breakdown"):
                writer.writerow([])
                yield buffer.getvalue()
                buffer.seek(0)
                buffer.truncate(0)
                writer.writerow(["Monthly", "Month", "Projected Value", "Expected Deals"])
                yield buffer.getvalue()
                buffer.seek(0)
                buffer.truncate(0)
                for item in velocity["monthly_breakdown"]:
                    writer.writerow(["Monthly", item["month"], fmt_currency(item["projected_value"]), str(item["expected_deals"])])
                    yield buffer.getvalue()
                    buffer.seek(0)
                    buffer.truncate(0)

            # === Deal-by-Deal ===
            if deal_forecasts:
                writer.writerow([])
                yield buffer.getvalue()
                buffer.seek(0)
                buffer.truncate(0)
                writer.writerow(["Deal", "Deal Name", "Value", "Probability", "Projected Value", "Est. Close Date", "Stage", "Pipeline"])
                yield buffer.getvalue()
                buffer.seek(0)
                buffer.truncate(0)
                for d in deal_forecasts:
                    writer.writerow([
                        "Deal",
                        d["deal_name"],
                        fmt_currency(d["deal_value"]),
                        f'{d["probability_weight"] * 100:.0f}%',
                        fmt_currency(d["projected_value"]),
                        d["estimated_close_date"] or "",
                        d["stage_name"],
                        d["pipeline_name"],
                    ])
                    yield buffer.getvalue()
                    buffer.seek(0)
                    buffer.truncate(0)

            # === What-If Scenario ===
            if what_if:
                writer.writerow([])
                yield buffer.getvalue()
                buffer.seek(0)
                buffer.truncate(0)
                writer.writerow(["What-If", "Stage", "Current Value", "Scenario Value", "Upside", "Close Rate"])
                yield buffer.getvalue()
                buffer.seek(0)
                buffer.truncate(0)
                writer.writerow([
                    "What-If",
                    what_if["stage_name"],
                    fmt_currency(what_if["current_projected_value"]),
                    fmt_currency(what_if["scenario_projected_value"]),
                    fmt_currency(what_if["upside"]),
                    f'{what_if["scenario_close_rate"] * 100:.0f}%',
                ])
                yield buffer.getvalue()
                buffer.seek(0)
                buffer.truncate(0)

        filename = f"forecast-{period_label.lower().replace(' ', '-')}.csv"
        response = StreamingHttpResponse(
            streaming_content=stream(),
            content_type="text/csv",
        )
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response
