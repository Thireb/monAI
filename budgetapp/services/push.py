"""Web Push bill alerts: the server key, subscriptions, the alert text and sending.

- The VAPID key pair (``WebPushKey``) is made on first use and kept in the database.
- A browser subscribes with an endpoint URL of its push service. The server sends requests
  to that URL, so only the known push services over HTTPS are accepted
  (``is_allowed_endpoint``).
- ``send_bill_alerts`` sends at most 1 alert a day to each browser. It lists the unpaid bills
  of this month that are due in ``ALERT_DAYS`` days or fewer, and the bill reminders whose
  alert window starts today. Run it once a day (``manage.py send_bill_alerts``).
"""

from __future__ import annotations

import base64
import json
import logging
from dataclasses import dataclass
from datetime import date
from urllib.parse import urlparse

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from django.contrib.auth.models import AbstractBaseUser
from py_vapid import Vapid02
from pywebpush import WebPushException, webpush

from budgetapp.bill_reminder_utils import reminder_start_date
from budgetapp.models import BillReminder, Budget, PushSubscription, WebPushKey
from budgetapp.services.bills import month_bills
from budgetapp.services.month import build_month_snapshot
from budgetapp.templatetags.app_format import money

logger = logging.getLogger(__name__)

# Unpaid bills due in this many days or fewer are in the alert.
ALERT_DAYS = 3

# The VAPID contact when the user has no email address.
FALLBACK_CONTACT = "admin@localhost"

# Hosts of the browser push services. A subscription must use one of them.
PUSH_HOSTS = (
    "fcm.googleapis.com",
    "updates.push.services.mozilla.com",
    "push.services.mozilla.com",
    "web.push.apple.com",
    "notify.windows.com",
)


@dataclass(frozen=True)
class Alert:
    """The text of 1 notification."""

    title: str
    body: str
    url: str = "/app/"


def is_allowed_endpoint(endpoint: str) -> bool:
    """Return True for an HTTPS URL of a known push service (or a subdomain of one)."""
    parsed = urlparse(endpoint)
    host = (parsed.hostname or "").lower()
    if parsed.scheme != "https" or not host:
        return False
    return any(host == known or host.endswith("." + known) for known in PUSH_HOSTS)


def server_key() -> WebPushKey:
    """Return the VAPID key pair; make it the first time."""
    key = WebPushKey.objects.order_by("id").first()
    if key is not None:
        return key
    private = ec.generate_private_key(ec.SECP256R1())
    pem = private.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    ).decode()
    raw = private.public_key().public_bytes(
        serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint
    )
    public = base64.urlsafe_b64encode(raw).decode().rstrip("=")
    return WebPushKey.objects.create(private_key=pem, public_key=public)


def save_subscription(
    user: AbstractBaseUser, endpoint: str, p256dh: str, auth: str, user_agent: str = ""
) -> PushSubscription:
    """Save the browser's subscription for ``user``. A browser has 1 owner: the last user."""
    subscription, _ = PushSubscription.objects.update_or_create(
        endpoint=endpoint,
        defaults={
            "user": user,
            "p256dh": p256dh,
            "auth": auth,
            "user_agent": user_agent[:200],
        },
    )
    return subscription


def send(subscription: PushSubscription, alert: Alert) -> bool:
    """Send ``alert`` to 1 browser. Delete a subscription that the push service says is gone.

    The push service gets the owner's email as the contact (a VAPID claim).
    """
    key = server_key()
    contact = getattr(subscription.user, "email", "") or FALLBACK_CONTACT
    try:
        webpush(
            subscription_info={
                "endpoint": subscription.endpoint,
                "keys": {"p256dh": subscription.p256dh, "auth": subscription.auth},
            },
            data=json.dumps({"title": alert.title, "body": alert.body, "url": alert.url}),
            vapid_private_key=Vapid02.from_pem(key.private_key.encode()),
            vapid_claims={"sub": f"mailto:{contact}"},
            ttl=12 * 60 * 60,
            timeout=10,
        )
    except WebPushException as exc:
        status = getattr(exc.response, "status_code", None)
        if status in (404, 410):
            subscription.delete()
        else:
            logger.warning("Web Push to subscription %s failed: %s", subscription.pk, exc)
        return False
    return True


def bill_alert(user: AbstractBaseUser, today: date) -> Alert | None:
    """The bill alert of ``user`` for ``today``, or ``None`` when no bill needs it."""
    parts: list[str] = []
    budget = Budget.objects.filter(user=user, month=today.replace(day=1)).first()
    if budget is not None:
        snap = build_month_snapshot(budget, today)
        for bill in month_bills(budget, snap, today):
            days = bill.days_until
            if bill.is_paid or days is None or not 0 <= days <= ALERT_DAYS:
                continue
            when = "today" if days == 0 else f"in {days} day{'s' if days != 1 else ''}"
            parts.append(f"{bill.name} {money(bill.amount)} {when}")
    for reminder in BillReminder.objects.filter(user=user, is_active=True):
        if reminder_start_date(reminder) == today:
            due = reminder.next_bill_date
            parts.append(f"{reminder.name} {money(reminder.amount)} on {due.day} {due:%b %Y}")
    if not parts:
        return None
    title = "1 bill coming up" if len(parts) == 1 else f"{len(parts)} bills coming up"
    return Alert(title=title, body=" · ".join(parts))


def send_bill_alerts(today: date) -> int:
    """Send today's bill alert to each browser that has not had one today. Return the count."""
    sent = 0
    waiting = PushSubscription.objects.exclude(last_alert_on=today).select_related("user")
    alerts: dict[int, Alert | None] = {}
    for subscription in waiting:
        if subscription.user_id not in alerts:
            alerts[subscription.user_id] = bill_alert(subscription.user, today)
        alert = alerts[subscription.user_id]
        if alert is None:
            continue
        if send(subscription, alert):
            subscription.last_alert_on = today
            subscription.save(update_fields=["last_alert_on"])
            sent += 1
    return sent
