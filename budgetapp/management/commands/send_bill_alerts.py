"""Send today's Web Push bill alerts. Run it once a day, for example with a systemd timer."""

from __future__ import annotations

from typing import Any

from django.core.management.base import BaseCommand
from django.utils import timezone

from budgetapp.services.push import send_bill_alerts


class Command(BaseCommand):
    """``manage.py send_bill_alerts``: 1 alert a day to each subscribed browser."""

    help = "Send today's bill alerts to the browsers that turned them on."

    def handle(self, *args: Any, **options: Any) -> None:
        """Send the alerts and print how many went out."""
        sent = send_bill_alerts(timezone.localdate())
        self.stdout.write(f"Sent {sent} bill alert{'s' if sent != 1 else ''}.")
