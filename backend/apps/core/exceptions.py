"""Custom exception handler for consistent error responses."""

from __future__ import annotations

from typing import Any

from rest_framework.response import Response
from rest_framework.views import exception_handler


def custom_exception_handler(exc: Exception, context: dict[str, Any]) -> Response | None:
    """Return consistent JSON error responses."""
    response = exception_handler(exc, context)

    if response is not None:
        errors = response.data
        # Wrap in consistent envelope
        response.data = {
            "error": True,
            "status_code": response.status_code,
            "detail": _extract_detail(errors),
            "errors": errors if isinstance(errors, dict) else None,
        }

    return response


def _extract_detail(errors: Any) -> str:
    """Extract a human-readable detail from DRF error dicts."""
    if isinstance(errors, str):
        return errors
    if isinstance(errors, list):
        return str(errors[0]) if errors else "Unknown error"
    if isinstance(errors, dict):
        first_key = next(iter(errors))
        val = errors[first_key]
        return _extract_detail(val)
    return str(errors)
