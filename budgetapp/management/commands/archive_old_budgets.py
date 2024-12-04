from django.core.management.base import BaseCommand
from django.utils import timezone
from budgetapp.models import Budget, ArchivedBudget
from django.db import transaction

class Command(BaseCommand):
    help = 'Archives budgets from previous years'

    def handle(self, *args, **options):
        current_date = timezone.now().date()
        
        # Get all non-archived budgets from previous years
        old_budgets = Budget.objects.filter(
            is_archived=False,
            month__year__lt=current_date.year
        )
        
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
            self.style.SUCCESS(f'Successfully archived {archived_count} budgets from previous years')
        ) 