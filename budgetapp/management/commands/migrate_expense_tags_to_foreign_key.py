"""Management command to migrate expense tags from CharField to ForeignKey."""
from __future__ import annotations

import argparse
from typing import Any

from django.core.management.base import BaseCommand

from budgetapp.models import Expense, Tag


class Command(BaseCommand):
    """Link legacy expense tag strings to Tag foreign keys."""

    help = "Migrate existing expense tags from CharField to ForeignKey relationship"

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        """Register command-line arguments.

        Args:
            parser: Argument parser provided by Django's command framework.
        """
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be migrated without actually updating expenses",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        """Update expenses to reference Tag rows instead of raw tag strings.

        Args:
            *args: Positional arguments from the management command runner.
            **options: Parsed command-line options.
        """
        dry_run = options["dry_run"]

        # Get all expenses that have a tag value and no tag_foreign_key
        expenses_to_migrate = Expense.objects.filter(
            tag__isnull=False, tag_foreign_key__isnull=True
        ).exclude(tag="none")

        total_expenses = expenses_to_migrate.count()
        updated_count = 0
        skipped_count = 0
        error_count = 0

        self.stdout.write(self.style.SUCCESS(f"Found {total_expenses} expenses to migrate..."))

        for expense in expenses_to_migrate:
            try:
                # Find the corresponding Tag object
                tag = Tag.objects.filter(name=expense.tag).first()

                if not tag:
                    self.stdout.write(
                        self.style.WARNING(
                            f"No Tag found for expense\n"
                            f'"{expense.name}" with tag value "{expense.tag}"'
                        )
                    )
                    error_count += 1
                    continue

                if dry_run:
                    self.stdout.write(
                        f'Would update expense "{expense.name}" (ID: {expense.id}) '
                        f'from tag "{expense.tag}" to tag_foreign_key "{tag.name}" (ID: {tag.id})'
                    )
                else:
                    expense.tag_foreign_key = tag
                    expense.save(update_fields=["tag_foreign_key"])
                    self.stdout.write(
                        f'Updated expense "{expense.name}" (ID: {expense.id}) '
                        f'to use tag "{tag.name}" (ID: {tag.id})'
                    )

                updated_count += 1

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f'Error updating expense "{expense.name}" (ID: {expense.id}): {str(e)}'
                    )
                )
                error_count += 1

        # Summary
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f"DRY RUN: Would update {updated_count} expenses, "
                    f"skip {skipped_count} expenses, "
                    f"encounter {error_count} errors"
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully updated {updated_count} expenses, "
                    f"skipped {skipped_count} expenses, "
                    f"encountered {error_count} errors"
                )
            )

        # Show remaining expenses that still need migration
        remaining_expenses = (
            Expense.objects.filter(tag__isnull=False, tag_foreign_key__isnull=True)
            .exclude(tag="none")
            .count()
        )

        if remaining_expenses > 0:
            self.stdout.write(
                self.style.WARNING(
                    f"Note: {remaining_expenses} expenses still need migration "
                    f"(likely due to missing Tag objects)"
                )
            )
        else:
            self.stdout.write(self.style.SUCCESS("All eligible expenses have been migrated!"))
