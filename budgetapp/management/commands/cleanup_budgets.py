from django.core.management.base import BaseCommand
from django.utils import timezone

from budgetapp.models import Budget


class Command(BaseCommand):
    help = "Removes all automatically created budgets except December 2024"

    def handle(self, *args, **options):
        # Keep only December 2024 budget
        deleted_count = Budget.objects.exclude(month__year=2024, month__month=12).delete()[0]

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully removed {deleted_count} automatically created budgets. Only December 2024 remains."
            )
        )
