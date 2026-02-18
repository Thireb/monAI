"""
Management command to create default expense categories.

This command creates a set of default categories for expense tracking.
Supports creating categories for a specific user or all users.
"""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from budgetapp.models import Category

User = get_user_model()

# Default categories with icons and colors
DEFAULT_CATEGORIES = [
    {
        "name": "Housing",
        "icon": "fa-home",
        "color": "#FF6B6B",
        "description": "Rent, mortgage, maintenance, and housing expenses",
    },
    {
        "name": "Transportation",
        "icon": "fa-car",
        "color": "#4ECDC4",
        "description": "Car payments, fuel, public transit, and maintenance",
    },
    {
        "name": "Food & Dining",
        "icon": "fa-utensils",
        "color": "#45B7D1",
        "description": "Groceries, restaurants, and food delivery",
    },
    {
        "name": "Utilities",
        "icon": "fa-bolt",
        "color": "#96CEB4",
        "description": "Electricity, water, gas, internet, and phone",
    },
    {
        "name": "Healthcare",
        "icon": "fa-hospital",
        "color": "#D4A5A5",
        "description": "Medical expenses, medications, and insurance",
    },
    {
        "name": "Entertainment",
        "icon": "fa-film",
        "color": "#9B59B6",
        "description": "Movies, games, streaming services, and hobbies",
    },
    {
        "name": "Shopping",
        "icon": "fa-shopping-bag",
        "color": "#E74C3C",
        "description": "Clothing, electronics, and personal items",
    },
    {
        "name": "Education",
        "icon": "fa-graduation-cap",
        "color": "#3498DB",
        "description": "Tuition, books, courses, and training",
    },
    {
        "name": "Savings",
        "icon": "fa-piggy-bank",
        "color": "#2ECC71",
        "description": "Emergency fund, investments, and long-term savings",
    },
    {
        "name": "Miscellaneous",
        "icon": "fa-ellipsis-h",
        "color": "#95A5A6",
        "description": "Other uncategorized expenses",
    },
]


class Command(BaseCommand):
    help = "Creates default expense categories for users"

    def add_arguments(self, parser):
        parser.add_argument(
            "--user-email",
            help="Create categories for a specific user (by email)",
        )
        parser.add_argument(
            "--all-users",
            action="store_true",
            help="Create categories for all users",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be created without making changes",
        )

    def create_categories_for_user(self, user, dry_run=False):
        """Create default categories for a specific user."""
        created_count = 0
        skipped_count = 0

        for category_data in DEFAULT_CATEGORIES:
            # Check if category already exists for this user
            existing = Category.objects.filter(
                user=user,
                name=category_data["name"],
            ).exists()

            if existing:
                skipped_count += 1
                continue

            if not dry_run:
                Category.objects.create(
                    user=user,
                    name=category_data["name"],
                    icon=category_data["icon"],
                    color=category_data["color"],
                    description=category_data["description"],
                )
            created_count += 1

        return created_count, skipped_count

    def handle(self, *args, **options):
        dry_run = options.get("dry_run", False)

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN - no changes will be made\n"))

        # Determine which users to process
        users = []

        if options.get("user_email"):
            try:
                user = User.objects.get(email=options["user_email"])
                users = [user]
            except User.DoesNotExist:
                self.stderr.write(
                    self.style.ERROR(f"User not found: {options['user_email']}")
                )
                return

        elif options.get("all_users"):
            users = User.objects.all()

        else:
            self.stderr.write(
                self.style.ERROR(
                    "Please specify either --user-email or --all-users\n"
                    "Examples:\n"
                    "  python manage.py create_default_categories --user-email user@example.com\n"
                    "  python manage.py create_default_categories --all-users"
                )
            )
            return

        if not users:
            self.stdout.write(self.style.WARNING("No users found."))
            return

        # Process each user
        total_created = 0
        total_skipped = 0

        for user in users:
            self.stdout.write(f"\nProcessing user: {user.email}")
            created, skipped = self.create_categories_for_user(user, dry_run)
            total_created += created
            total_skipped += skipped
            self.stdout.write(f"  Created: {created}, Skipped (already exist): {skipped}")

        # Summary
        action = "Would create" if dry_run else "Created"
        self.stdout.write(
            self.style.SUCCESS(
                f"\n{action} {total_created} categories, skipped {total_skipped}"
            )
        )
