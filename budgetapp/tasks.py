"""Celery tasks for scheduled budget maintenance."""

from __future__ import annotations

from django.db import transaction
from django.utils import timezone

from celery import shared_task
from django_celery_beat.models import CrontabSchedule, PeriodicTask

from .models import ArchivedBudget, Budget


@shared_task
def archive_old_budgets() -> str:
    """Archive budgets from previous calendar years.

    Returns:
        Human-readable summary of how many budgets were archived.
    """
    setup_periodic_tasks()

    current_date = timezone.now().date()
    old_budgets = Budget.objects.filter(is_archived=False, month__year__lt=current_date.year)

    archived_count = 0
    with transaction.atomic():
        for budget in old_budgets:
            if not ArchivedBudget.objects.filter(budget=budget).exists():
                ArchivedBudget.objects.create(budget=budget)
                budget.is_archived = True
                budget.save()
                archived_count += 1

    return f"Successfully archived {archived_count} budgets from previous years"


def setup_periodic_tasks() -> None:
    """Ensure the nightly archive task is registered in django-celery-beat."""
    if not PeriodicTask.objects.filter(name="Archive old budgets").exists():
        schedule, _ = CrontabSchedule.objects.get_or_create(
            hour=0, minute=0, timezone=timezone.get_current_timezone()
        )

        PeriodicTask.objects.get_or_create(
            name="Archive old budgets",
            task="budgetapp.tasks.archive_old_budgets",
            crontab=schedule,
            enabled=True,
        )
