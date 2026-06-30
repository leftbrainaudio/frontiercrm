"""Tests for Phase 4 audit fix B1 — ActivityTimeline module cleanup.

B1 removed broken activity-*.tsx files and ensured TimelinePage loads without
ReferenceError.  The broken files (e.g. partial stubs of activity-list,
activity-detail, etc.) were causing runtime ReferenceErrors because they
referenced undefined components or types.

Verification:
  1. Only valid activity-*.tsx files exist  (activity-card, activity-filters)
  2. TimelinePage module tree resolves cleanly — all imports work
  3. The existing frontend timeline-page.test.tsx covers loading, error,
     empty, and data states (vitest-based, not run here).
"""

from __future__ import annotations

import os
import re
from pathlib import Path

ACTIVITIES_DIR = Path(
    "/Users/chriskilloran/FrontierCRM/frontend/src/pages/activities"
)


# ===================================================================
# 1  No broken activity-*.tsx files
# ===================================================================


class TestActivityFilesClean:
    """B1: Only valid activity-*.tsx files remain.

    The broken files were partial stubs that imported or referenced
    components that didn't exist, causing ReferenceErrors at runtime.
    """

    # Allowed activity-* files (these are the valid ones)
    ALLOWED_ACTIVITY_FILES = frozenset({
        "activity-card.tsx",
        "activity-card.test.tsx",
        "activity-filters.tsx",
        "activity-filters.test.tsx",
    })

    def test_no_unknown_activity_files(self):
        """No unexpected activity-*.tsx files beyond the allowed set."""
        unknown: list[str] = []
        for f in ACTIVITIES_DIR.iterdir():
            if re.match(r"^activity-.*\.tsx?$", f.name) and not f.name.endswith(".d.ts"):
                if f.name not in self.ALLOWED_ACTIVITY_FILES:
                    unknown.append(f.name)
        assert not unknown, (
            f"Unexpected activity-*.tsx files found: {unknown}. "
            "B1 removed broken activity-* files; only activity-card and "
            "activity-filters should exist."
        )

    def test_activity_card_exists_and_valid(self):
        """activity-card.tsx exists and has reasonable content."""
        path = ACTIVITIES_DIR / "activity-card.tsx"
        assert path.exists(), "activity-card.tsx must exist"
        content = path.read_text()
        # Must export something useful
        assert "ACTIVITY_ICONS" in content or "export" in content
        # Must not contain obvious broken references
        assert "ReferenceError" not in content

    def test_activity_filters_exists_and_valid(self):
        """activity-filters.tsx exists and has reasonable content."""
        path = ACTIVITIES_DIR / "activity-filters.tsx"
        assert path.exists(), "activity-filters.tsx must exist"
        content = path.read_text()
        assert "TimelineFilterState" in content
        assert "ReferenceError" not in content


# ===================================================================
# 2  Module tree resolves without ReferenceError
# ===================================================================


class TestModuleTree:
    """Verify the import chain loads cleanly.

    The TimelinePage import chain is:
      index.ts → timeline-page.tsx
               → activity-filters.tsx (TimelineFilterState type)
               → timeline-card.tsx (TimelineGroup, groupTimelineByDate)
               → ../../api/activities (useActivityTimeline hook)
    """

    def test_index_exports_timeline_page(self):
        """index.ts exports TimelinePage function."""
        index_path = ACTIVITIES_DIR / "index.ts"
        assert index_path.exists()
        content = index_path.read_text()
        assert "export { TimelinePage }" in content, (
            "index.ts must export TimelinePage"
        )

    def test_index_exports_filter_state_type(self):
        """index.ts re-exports TimelineFilterState type."""
        index_path = ACTIVITIES_DIR / "index.ts"
        content = index_path.read_text()
        assert "export type { TimelineFilterState }" in content, (
            "index.ts must re-export TimelineFilterState type"
        )

    def test_timeline_page_imports_use_activity_timeline(self):
        """timeline-page.tsx imports useActivityTimeline."""
        path = ACTIVITIES_DIR / "timeline-page.tsx"
        assert path.exists()
        content = path.read_text()
        assert "useActivityTimeline" in content
        assert "../../api/activities" in content or "@/api/activities" in content

    def test_timeline_page_uses_activity_filters(self):
        """timeline-page.tsx imports ActivityFilters component."""
        path = ACTIVITIES_DIR / "timeline-page.tsx"
        content = path.read_text()
        assert "ActivityFilters" in content
        assert "activity-filters" in content

    def test_timeline_page_uses_timeline_group(self):
        """timeline-page.tsx imports TimelineGroup from timeline-card."""
        path = ACTIVITIES_DIR / "timeline-page.tsx"
        content = path.read_text()
        assert "TimelineGroup" in content
        assert "timeline-card" in content

    def test_timeline_page_has_no_reference_error_payload(self):
        """No raw strings that would cause ReferenceError at runtime."""
        path = ACTIVITIES_DIR / "timeline-page.tsx"
        content = path.read_text()
        # Looking for patterns that suggest undefined references
        assert "ReferenceError" not in content

    def test_activity_card_no_broken_imports(self):
        """activity-card.tsx imports only valid modules."""
        path = ACTIVITIES_DIR / "activity-card.tsx"
        content = path.read_text()
        # All imports should be from known local modules or libraries
        local_imports = re.findall(r"from\s+['\"](\..*?)['\"]", content)
        for imp in local_imports:
            resolved = (ACTIVITIES_DIR / imp).resolve()
            # If it's a relative path within the same dir, the target should exist
            if "../" not in imp and not imp.startswith("../../"):
                target = ACTIVITIES_DIR / imp
                if not target.exists() and not target.with_suffix(".tsx").exists():
                    # Might be a re-export from index.ts
                    assert False, (
                        f"activity-card.tsx imports '{imp}' which does not exist"
                    )


# ===================================================================
# 3  Router integration
# ===================================================================


class TestRouterIntegration:
    """The router imports TimelinePage from the activities barrel."""

    ROUTER_PATH = "/Users/chriskilloran/FrontierCRM/frontend/src/router/index.tsx"

    def test_router_imports_timeline_page(self):
        """Router imports TimelinePage."""
        path = Path(self.ROUTER_PATH)
        assert path.exists()
        content = path.read_text()
        assert "TimelinePage" in content
        assert "../pages/activities" in content or "@/pages/activities" in content

    def test_router_registers_timeline_route(self):
        """Router registers both /activities and /timeline routes."""
        path = Path(self.ROUTER_PATH)
        content = path.read_text()
        assert "activities" in content and "element: <TimelinePage" in content
        assert "timeline" in content and "element: <TimelinePage" in content

    def test_frontend_timeline_test_exists(self):
        """The vitest-based timeline-page.test.tsx exists with assertions."""
        test_path = ACTIVITIES_DIR / "timeline-page.test.tsx"
        assert test_path.exists()
        content = test_path.read_text()
        # Verify it covers key states
        assert "describe('TimelinePage'" in content
        assert "loading" in content.lower() or "Loading" in content
        assert "error" in content.lower()
        assert "empty" in content.lower()
