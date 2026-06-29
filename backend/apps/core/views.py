"""Core views for FrontierCRM."""

from pathlib import Path

from django.http import FileResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET

# Path to built frontend
FRONTEND_DIST = Path(__file__).resolve().parent.parent.parent.parent / "frontend" / "dist"


@require_GET
@csrf_exempt
def spa_serve(request, path: str = "") -> FileResponse:
    """Serve the frontend SPA from the dist directory.

    Static assets (JS, CSS, images) are served directly from dist.
    All other routes return index.html for React Router.
    Uses request.path to resolve the correct file regardless of URL prefix.
    """
    if not FRONTEND_DIST.exists():
        raise Http404("Frontend not built yet")

    # Resolve the requested file path relative to dist
    # Strip leading / from request.path to get the relative path
    rel_path = request.path.lstrip("/")

    # If no specific file requested (root /), or path points to a directory, serve index.html
    if not rel_path:
        return _serve_index()

    file_path = (FRONTEND_DIST / rel_path).resolve()

    # Serve the actual file if it exists and is a file (not a directory) and inside dist
    if file_path.exists() and file_path.is_file() and str(file_path).startswith(str(FRONTEND_DIST.resolve())):
        return FileResponse(open(file_path, "rb"))

    # Fallback: serve index.html (SPA catch-all for React Router)
    return _serve_index()


def _serve_index() -> FileResponse:
    """Serve the SPA's index.html."""
    index_path = (FRONTEND_DIST / "index.html").resolve()
    if index_path.exists():
        return FileResponse(open(index_path, "rb"))
    raise Http404("Frontend not built yet")
