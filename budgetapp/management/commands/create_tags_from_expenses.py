import random

from django.core.management.base import BaseCommand

from budgetapp.models import Expense, Tag


class Command(BaseCommand):
    help = "Create Tag objects from existing manual tags in Expense model"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be created without actually creating tags",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]

        # Get all unique tag values from expenses
        existing_tags = Expense.objects.values_list("tag", flat=True).distinct()

        # Predefined colors for tags
        colors = [
            "#2196f3",
            "#4caf50",
            "#ff9800",
            "#e91e63",
            "#9c27b0",
            "#00bcd4",
            "#ff5722",
            "#795548",
            "#607d8b",
            "#3f51b5",
            "#009688",
            "#ffc107",
            "#8bc34a",
            "#ff4081",
            "#673ab7",
        ]

        created_count = 0
        skipped_count = 0

        self.stdout.write(self.style.SUCCESS("Starting tag migration..."))

        for tag_value in existing_tags:
            if tag_value == "none":
                continue

            # Check if tag already exists
            if Tag.objects.filter(name=tag_value).exists():
                self.stdout.write(f'Skipping "{tag_value}" - already exists')
                skipped_count += 1
                continue

            # Create tag with random color
            color = random.choice(colors)

            if dry_run:
                self.stdout.write(f'Would create tag: "{tag_value}" with color {color}')
            else:
                tag = Tag.objects.create(
                    name=tag_value,
                    description="Migrated from existing expenses",
                    color=color,
                )
                self.stdout.write(f'Created tag: "{tag.name}" with color {tag.color}')

            created_count += 1

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f"DRY RUN: Would create {created_count} tags, skip {skipped_count} existing"
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully created {created_count} tags, skipped {skipped_count} existing"
                )
            )
