"""Management command to remove automatically created budgets except December 2024."""
from __future__ import annotations

from typing import Any

from django.core.management.base import BaseCommand

from budgetapp.models import Budget


class Command(BaseCommand):
    """Delete all budgets except the December 2024 record."""

    help = "Removes all automatically created budgets except December 2024"

    def handle(self, *args: Any, **options: Any) -> None:
        """Remove budgets outside December 2024.

        Args:
            *args: Positional arguments from the management command runner.
            **options: Keyword options from the management command runner.
        """
        # Keep only December 2024 budget
        deleted_count = Budget.objects.exclude(month__year=2024, month__month=12).delete()[0]

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully removed {deleted_count} automatically created budgets. "
                f"Only December 2024 remains."
            )
        )
