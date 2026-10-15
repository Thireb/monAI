"""Health-check endpoint for monitoring clients."""

from __future__ import annotations

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response


@api_view(["GET"])
@permission_classes([AllowAny])
def health(request: Request) -> Response:
    """Lightweight liveness probe for a monitor.

    No sensitive data is returned; LAN-only use is still recommended.

    Args:
        request: Incoming HTTP request (unused).

    Returns:
        JSON payload with ``status: ok``.
    """
    return Response({"status": "ok"})
