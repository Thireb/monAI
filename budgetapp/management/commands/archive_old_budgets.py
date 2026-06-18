"""Management command to archive budgets from previous years."""
from __future__ import annotations

from typing import Any

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from budgetapp.models import ArchivedBudget, Budget


class Command(BaseCommand):
    """Archive budgets from years before the current calendar year."""

    help = "Archives budgets from previous years"

    def handle(self, *args: Any, **options: Any) -> None:
        """Find old budgets and move them into the archived state.

        Args:
            *args: Positional arguments from the management command runner.
            **options: Keyword options from the management command runner.
        """
        current_date = timezone.now().date()

        # Get all non-archived budgets from previous years
        old_budgets = Budget.objects.filter(is_archived=False, month__year__lt=current_date.year)

        archived_count = 0
        with transaction.atomic():
            for budget in old_budgets:
                # Check if not already archived
                if not ArchivedBudget.objects.filter(budget=budget).exists():
                    ArchivedBudget.objects.create(budget=budget)
                    budget.is_archived = True
                    budget.save()
                    archived_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully archived {archived_count} budgets from previous years"
            )
        )
