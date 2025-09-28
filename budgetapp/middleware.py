import logging
import time

from django.urls import resolve
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger("budgetapp.middleware")


class RequestLoggingMiddleware(MiddlewareMixin):
    """
    Middleware to log detailed information about each request including:
    - HTTP method and URL
    - View function/class name and file path
    - URL pattern name
    - Request processing time
    """

    def process_request(self, request):
        """Store request start time and view info for later logging."""
        request._start_time = time.time()

        try:
            # Resolve the URL to get view information
            resolver_match = resolve(request.path_info)
            view_func = resolver_match.func

            # Get view information
            if hasattr(view_func, "view_class"):
                # Class-based view
                view_class = view_func.view_class
                view_name = f"{view_class.__module__}.{view_class.__name__}"
                view_file = view_class.__module__.replace(".", "/") + ".py"
            else:
                # Function-based view
                view_name = f"{view_func.__module__}.{view_func.__name__}"
                view_file = view_func.__module__.replace(".", "/") + ".py"

            # Get URL pattern name
            url_name = resolver_match.url_name or "unnamed"
            namespace = resolver_match.namespace or ""
            full_url_name = f"{namespace}:{url_name}" if namespace else url_name

            # Store for response logging
            request._view_info = {
                "view_name": view_name,
                "view_file": view_file,
                "url_name": full_url_name,
            }

        except Exception as e:
            logger.warning(f"Could not resolve view for {request.path}: {e}")
            request._view_info = None

    def process_response(self, request, response):
        """Log complete request/response details in a single line."""
        if hasattr(request, "_start_time"):
            processing_time = time.time() - request._start_time

            # Get status code color for better visibility
            status_color = (
                "🟢"
                if 200 <= response.status_code < 300
                else "🟡" if 300 <= response.status_code < 400 else "🔴"
            )

            if hasattr(request, "_view_info") and request._view_info:
                view_info = request._view_info
                logger.info(
                    f"{status_color} {response.status_code} {request.method} {request.path} "
                    f"→ {view_info['view_name']} [{view_info['url_name']}] "
                    f"({processing_time:.3f}s)"
                )
            else:
                logger.info(
                    f"{status_color} {response.status_code} {request.method} {request.path} "
                    f"({processing_time:.3f}s)"
                )

        return response

    def process_exception(self, request, exception):
        """Log exceptions that occur during request processing."""
        if hasattr(request, "_view_info") and request._view_info:
            view_info = request._view_info
            logger.error(
                f"🔥 EXCEPTION in {request.method} {request.path} "
                f"→ {view_info['view_name']} [{view_info['url_name']}]: {exception}",
                exc_info=True,
            )
        else:
            logger.error(
                f"🔥 EXCEPTION in {request.method} {request.path}: {exception}", exc_info=True
            )
