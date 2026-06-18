"""Mobile email/password token authentication for the REST API."""

from __future__ import annotations

from typing import Any

from django.contrib.auth import authenticate
from django.contrib.auth.models import AbstractBaseUser
from rest_framework import serializers
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView


class MobileEmailTokenSerializer(serializers.Serializer):
    """Validate email/password credentials for mobile token issuance."""

    email = serializers.EmailField()
    password = serializers.CharField(
        trim_whitespace=False,
        style={"input_type": "password"},
    )

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        """Authenticate the user and attach them to validated attrs.

        Args:
            attrs: Raw serializer input containing email and password.

        Returns:
            Validated attrs with ``user`` set on success.

        Raises:
            ValidationError: When credentials are invalid or the user is inactive.
        """
        email = attrs["email"]
        password = attrs["password"]
        request = self.context.get("request")
        user = authenticate(request=request, email=email, password=password)
        if user is None or not user.is_active:
            raise serializers.ValidationError("Invalid email or password.")
        attrs["user"] = user
        return attrs


class MobileObtainAuthTokenView(APIView):
    """Exchange email/password JSON for a DRF authtoken.

    POST body: ``{"email": "...", "password": "..."}``
    Response: ``{"token": "..."}``
    """

    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        """Validate credentials and return or create an auth token.

        Args:
            request: Request with email and password in the body.

        Returns:
            JSON response containing the token key.
        """
        serializer = MobileEmailTokenSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        user: AbstractBaseUser = serializer.validated_data["user"]
        token, _ = Token.objects.get_or_create(user=user)
        return Response({"token": token.key})
