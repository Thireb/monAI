from django.contrib.auth import authenticate, get_user_model
from rest_framework import serializers
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView


class MobileEmailTokenSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(
        trim_whitespace=False,
        style={"input_type": "password"},
    )

    def validate(self, attrs):
        email = attrs["email"]
        password = attrs["password"]
        request = self.context.get("request")
        user = authenticate(request=request, email=email, password=password)
        if user is None or not user.is_active:
            raise serializers.ValidationError("Invalid email or password.")
        attrs["user"] = user
        return attrs


class MobileObtainAuthTokenView(APIView):
    """POST JSON { \"email\", \"password\" } -> { \"token\": \"...\" } for mobile clients."""

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = MobileEmailTokenSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        token, _ = Token.objects.get_or_create(user=user)
        return Response({"token": token.key})
