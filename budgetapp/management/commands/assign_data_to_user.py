"""
Management command to assign orphaned data to a specific user.

This command is useful when:
1. Migrating from single-user to multi-user setup
2. Reassigning data after user deletion
3. Fixing orphaned records
"""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from budgetapp.models import Budget, Category, Debt, Goal, Tag

User = get_user_model()


class Command(BaseCommand):
    help = "Assign orphaned data (null user) to a specific user"

    def add_arguments(self, parser):
        parser.add_argument(
            "--email",
            required=True,
            help="Email of the user to assign data to",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be changed without making changes",
        )

    def handle(self, *args, **options):
        email = options["email"]
        dry_run = options.get("dry_run", False)

        # Get the user
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            self.stderr.write(self.style.ERROR(f"User with email {email} not found."))
            return

        self.stdout.write(f"\nAssigning orphaned data to user: {user.email}")
        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN - no changes will be made\n"))

        # Models with user foreign key
        models = [
            ("Budgets", Budget),
            ("Categories", Category),
            ("Tags", Tag),
            ("Debts", Debt),
            ("Goals", Goal),
        ]

        total_updated = 0

        for name, model in models:
            orphaned = model.objects.filter(user__isnull=True)
            count = orphaned.count()

            if count > 0:
                self.stdout.write(f"  {name}: {count} orphaned record(s)")

                if not dry_run:
                    orphaned.update(user=user)
                    self.stdout.write(self.style.SUCCESS(f"    -> Assigned to {user.email}"))

                total_updated += count
            else:
                self.stdout.write(f"  {name}: No orphaned records")

        if dry_run:
            self.stdout.write(
                f"\nDRY RUN complete. Would have assigned {total_updated} record(s) to {user.email}"
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f"\nDone! Assigned {total_updated} record(s) to {user.email}")
            )

