from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


@api_view(["GET"])
@permission_classes([AllowAny])
def mobile_health(request):
    """
    Lightweight endpoint for the Flutter app to detect when the dev server is up.
    No sensitive data; LAN use only is still recommended.
    """
    return Response({"status": "ok"})
