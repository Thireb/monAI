from pathlib import Path

from django.http import HttpResponse


def service_worker(request):
    """Serve the service worker file with correct content type."""
    import logging

    logger = logging.getLogger("budgetapp")

    # __file__ is budgetapp/views.py, so:
    # .parent = budgetapp/
    # .parent.parent = django_budget_tracker/ (project root)
    BASE_DIR = Path(__file__).resolve().parent.parent
    sw_path = BASE_DIR / "budgetapp" / "static" / "js" / "service-worker.js"

    logger.info(f"Service worker requested. Path: {sw_path}, Exists: {sw_path.exists()}")

    if not sw_path.exists():
        logger.error(f"Service worker file not found at: {sw_path}")
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
        logger.error(f"Error serving service worker: {e}")
        return HttpResponse(f"Error: {str(e)}", status=500, content_type="text/plain")
