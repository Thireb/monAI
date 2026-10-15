"""Web Push for the new UI: the server key, subscribe, unsubscribe and a test alert."""

from __future__ import annotations

import json

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.views import View

from budgetapp.models import PushSubscription
from budgetapp.services.push import Alert, is_allowed_endpoint, save_subscription, send, server_key

from .goals import toast


class PushKeyView(LoginRequiredMixin, View):
    """The server's public key, for ``pushManager.subscribe``."""

    def get(self, request: HttpRequest) -> JsonResponse:
        """Return the key as URL-safe base64."""
        return JsonResponse({"public_key": server_key().public_key})


class PushSubscribeView(LoginRequiredMixin, View):
    """Save this browser's push subscription (JSON from ``PushSubscription.toJSON()``)."""

    def post(self, request: HttpRequest) -> JsonResponse:
        """Check and save the subscription."""
        try:
            data = json.loads(request.body)
            endpoint = str(data["endpoint"])
            p256dh = str(data["keys"]["p256dh"])
            auth = str(data["keys"]["auth"])
        except (ValueError, KeyError, TypeError):
            return JsonResponse({"error": "This is not a push subscription."}, status=400)
        if not is_allowed_endpoint(endpoint) or len(endpoint) > 500:
            return JsonResponse({"error": "This push service is not supported."}, status=400)
        if not (0 < len(p256dh) <= 200 and 0 < len(auth) <= 100):
            return JsonResponse({"error": "This is not a push subscription."}, status=400)
        user_agent = request.headers.get("User-Agent", "")
        save_subscription(request.user, endpoint, p256dh, auth, user_agent)
        return JsonResponse({"ok": True})


class PushUnsubscribeView(LoginRequiredMixin, View):
    """Forget this browser's subscription."""

    def post(self, request: HttpRequest) -> JsonResponse:
        """Delete the user's subscription with the given endpoint."""
        try:
            endpoint = str(json.loads(request.body)["endpoint"])
        except (ValueError, KeyError, TypeError):
            return JsonResponse({"error": "No endpoint."}, status=400)
        PushSubscription.objects.filter(user=request.user, endpoint=endpoint).delete()
        return JsonResponse({"ok": True})


class PushTestView(LoginRequiredMixin, View):
    """Send a test alert to all of the user's browsers; answer with a toast."""

    def post(self, request: HttpRequest) -> HttpResponse:
        """Send the test and say how many browsers got it."""
        subscriptions = list(PushSubscription.objects.filter(user=request.user))
        if not subscriptions:
            return toast(request, "Turn on bill alerts on this device first.", error=True)
        alert = Alert(title="monAI bill alerts work", body="You will see your bills here.")
        sent = sum(send(subscription, alert) for subscription in subscriptions)
        if not sent:
            return toast(request, "The push service did not take the test. Try again.", error=True)
        return toast(request, f"Sent a test to {sent} device{'s' if sent != 1 else ''}.")
