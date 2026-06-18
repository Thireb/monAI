"""Miscellaneous HTTP views for the budgetapp package."""

from __future__ import annotations

import logging
from pathlib import Path

from django.http import HttpRequest, HttpResponse

logger = logging.getLogger("budgetapp")


def service_worker(request: HttpRequest) -> HttpResponse:
    """Serve the PWA service worker with correct content type and cache headers.

    Args:
        request: Incoming HTTP request (unused).

    Returns:
        Service worker JavaScript or an error response.
    """
    BASE_DIR = Path(__file__).resolve().parent.parent
    sw_path = BASE_DIR / "static" / "js" / "service-worker.js"

    logger.info("Service worker requested. Path: %s, Exists: %s", sw_path, sw_path.exists())

    if not sw_path.exists():
        logger.error("Service worker file not found at: %s", sw_path)
        return HttpResponse("Service worker not found", status=404, content_type="text/plain")

    try:
        with open(sw_path, "r", encoding="utf-8") as f:
            content = f.read()
        response = HttpResponse(content, content_type="application/javascript; charset=utf-8")
        response["Service-Worker-Allowed"] = "/"
        response["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response["Pragma"] = "no-cache"
        response["Expires"] = "0"
        logger.info("Service worker served successfully")
        return response
    except Exception as e:
        logger.error("Error serving service worker: %s", e)
        return HttpResponse(f"Error: {str(e)}", status=500, content_type="text/plain")
