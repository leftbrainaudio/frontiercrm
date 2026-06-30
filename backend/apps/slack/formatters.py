"""Slack Block Kit message formatters — build rich Slack payloads from Activities."""

from __future__ import annotations

from typing import Any

from apps.activities.models import Activity


class SlackMessageFormatter:
    """Build Slack Block Kit payloads from Activity records."""

    FORMATTERS: dict[str, callable] = {}

    @classmethod
    def register(cls, activity_type: str):
        """Decorator to register a formatter for an activity type."""

        def wrapper(func):
            cls.FORMATTERS[activity_type] = func
            return func

        return wrapper

    @classmethod
    def format(cls, activity: Activity) -> dict[str, Any]:
        """Return a Slack-compatible block payload for the given activity."""
        formatter = cls.FORMATTERS.get(activity.activity_type)
        if formatter is None:
            return cls._generic_format(activity)
        return formatter(activity)

    @classmethod
    def _generic_format(cls, activity: Activity) -> dict[str, Any]:
        return {
            "text": f"[{activity.activity_type}] {activity.title}",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*{activity.title}*\n{activity.description}",
                    },
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": f"FrontierCRM · {activity.created_at.isoformat()}",
                        }
                    ],
                },
            ],
        }


# ── Register built-in formatters ────────────────────────────────────────


@SlackMessageFormatter.register("deal_stage_change")
def _format_deal_stage_change(activity: Activity) -> dict[str, Any]:
    meta = activity.metadata
    return {
        "blocks": [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": "🔄 Deal Stage Changed"},
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Deal:*\n<https://app.frontiercrm.com/deals/{activity.entity_id}|{meta.get('deal_name', 'Unknown')}>",
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Value:*\n${meta.get('value', '—')}",
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*From:*\n{meta.get('from_stage', '?')}",
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*To:*\n{meta.get('to_stage', '?')}",
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Owner:*\n{meta.get('owner_name', '—')}",
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Pipeline:*\n{meta.get('pipeline_name', '—')}",
                    },
                ],
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"FrontierCRM · {activity.created_at.isoformat()}",
                    }
                ],
            },
        ],
    }


@SlackMessageFormatter.register("deal_status_change")
def _format_deal_status_change(activity: Activity) -> dict[str, Any]:
    meta = activity.metadata
    new_status = meta.get("new_status", "")

    if new_status == "won":
        emoji = "🎉"
        title = "Deal Won!"
    elif new_status == "lost":
        emoji = "❌"
        title = "Deal Lost"
    else:
        emoji = "📋"
        title = f"Deal Status: {new_status}"

    fields = [
        {
            "type": "mrkdwn",
            "text": f"*Deal:*\n<https://app.frontiercrm.com/deals/{activity.entity_id}|{meta.get('deal_name', 'Unknown')}>",
        },
        {
            "type": "mrkdwn",
            "text": f"*Value:*\n${meta.get('value', '—')}",
        },
        {
            "type": "mrkdwn",
            "text": f"*Owner:*\n{meta.get('owner_name', '—')}",
        },
        {
            "type": "mrkdwn",
            "text": f"*Pipeline:*\n{meta.get('pipeline_name', '—')}",
        },
    ]

    if new_status == "lost" and meta.get("lost_reason"):
        fields.append(
            {
                "type": "mrkdwn",
                "text": f"*Lost Reason:*\n{meta['lost_reason']}",
            }
        )

    return {
        "blocks": [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": f"{emoji} {title}"},
            },
            {"type": "section", "fields": fields},
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"FrontierCRM · {activity.created_at.isoformat()}",
                    }
                ],
            },
        ],
    }


@SlackMessageFormatter.register("email")
def _format_email(activity: Activity) -> dict[str, Any]:
    meta = activity.metadata
    direction = meta.get("direction", "inbound")
    header = "📤 Email Sent" if direction == "outbound" else "📧 New Email"

    return {
        "blocks": [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": header},
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*From:*\n{meta.get('from_name', '?')} <{meta.get('from_email', '?')}>",
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Subject:*\n{meta.get('subject', '(no subject)')}",
                    },
                ],
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"```{meta.get('snippet', '')[:300]}```",
                },
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"FrontierCRM · {activity.created_at.isoformat()}",
                    }
                ],
            },
        ],
    }