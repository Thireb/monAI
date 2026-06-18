"""Model signals for cache invalidation and related side effects."""

from __future__ import annotations

from typing import Any

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from budgetapp.calendar_cache import bump_user_cache_version
from budgetapp.models import Budget


@receiver(post_save, sender=Budget)
@receiver(post_delete, sender=Budget)
def invalidate_calendar_cache_on_budget_change(
    sender: type[Budget],
    instance: Budget,
    **kwargs: Any,
) -> None:
    """Bump calendar cache version when a budget is saved or deleted."""
    if instance.user_id:
        bump_user_cache_version(instance.user_id)
