"""Request logging middleware for development and diagnostics."""

from __future__ import annotations

import logging
import time

from django.http import HttpRequest, HttpResponse
from django.urls import Resolver404, resolve
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger("budgetapp.middleware")


class RequestLoggingMiddleware(MiddlewareMixin):
    """Log HTTP method, path, view name, and processing time for each request."""

    def process_request(self, request: HttpRequest) -> None:
        """Store request start time and resolved view info for response logging."""
        request._start_time = time.time()

        try:
            resolver_match = resolve(request.path_info)
            view_func = resolver_match.func

            if hasattr(view_func, "view_class"):
                view_class = view_func.view_class
                view_name = f"{view_class.__module__}.{view_class.__name__}"
                view_file = view_class.__module__.replace(".", "/") + ".py"
            else:
                view_name = f"{view_func.__module__}.{view_func.__name__}"
                view_file = view_func.__module__.replace(".", "/") + ".py"

            url_name = resolver_match.url_name or "unnamed"
            namespace = resolver_match.namespace or ""
            full_url_name = f"{namespace}:{url_name}" if namespace else url_name

            request._view_info = {
                "view_name": view_name,
                "view_file": view_file,
                "url_name": full_url_name,
            }

        except (Resolver404, Exception) as e:
            logger.warning("Could not resolve view for %s: %s", request.path, e)
            request._view_info = None

    def process_response(self, request: HttpRequest, response: HttpResponse) -> HttpResponse:
        """Log complete request/response details in a single line."""
        if hasattr(request, "_start_time"):
            processing_time = time.time() - request._start_time

            status_color = (
                "🟢"
                if 200 <= response.status_code < 300
                else "🟡" if 300 <= response.status_code < 400 else "🔴"
            )

            if hasattr(request, "_view_info") and request._view_info:
                view_info = request._view_info
                logger.info(
                    "%s %s %s %s → %s [%s] (%.3fs)",
                    status_color,
                    response.status_code,
                    request.method,
                    request.path,
                    view_info["view_name"],
                    view_info["url_name"],
                    processing_time,
                )
            else:
                logger.info(
                    "%s %s %s %s (%.3fs)",
                    status_color,
                    response.status_code,
                    request.method,
                    request.path,
                    processing_time,
                )

        return response

    def process_exception(
        self,
        request: HttpRequest,
        exception: BaseException,
    ) -> None:
        """Log exceptions that occur during request processing."""
        if hasattr(request, "_view_info") and request._view_info:
            view_info = request._view_info
            logger.error(
                "🔥 EXCEPTION in %s %s → %s [%s]: %s",
                request.method,
                request.path,
                view_info["view_name"],
                view_info["url_name"],
                exception,
                exc_info=True,
            )
        else:
            logger.error(
                "🔥 EXCEPTION in %s %s: %s",
                request.method,
                request.path,
                exception,
                exc_info=True,
            )
