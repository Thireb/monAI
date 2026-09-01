"""Django admin registrations for budgetapp models."""

from __future__ import annotations

from django.contrib import admin

from .models import (
    Budget,
    Debt,
    DebtTransaction,
    Expense,
    Goal,
    GoalContribution,
    Tag,
    TagTransfer,
)


@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    """Admin interface for monthly budgets."""

    list_display = ("month", "created_at")
    list_filter = ("month",)


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    """Admin interface for budget expense line items."""

    list_display = ("name", "amount", "budget", "is_recurring")
    list_filter = ("is_recurring", "budget__month")
    search_fields = ("name",)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Admin interface for user-defined expense tags."""

    list_display = ("name", "description", "color", "is_active", "created_at")
    list_filter = ("is_active", "created_at")
    search_fields = ("name", "description")
    readonly_fields = ("created_at", "updated_at")


@admin.register(TagTransfer)
class TagTransferAdmin(admin.ModelAdmin):
    """Admin interface for account-tag transfers within a budget."""

    list_display = ("budget", "from_tag", "to_tag", "amount", "date", "updated_at")
    list_filter = ("date", "budget__month")
    search_fields = ("note", "from_tag__name", "to_tag__name")
    readonly_fields = ("created_at", "updated_at")


@admin.register(Goal)
class GoalAdmin(admin.ModelAdmin):
    """Admin interface for savings goals."""

    list_display = (
        "name",
        "target_amount",
        "current_amount",
        "progress_percentage",
        "target_date",
        "category",
        "is_active",
    )
    list_filter = ("category", "is_active")
    search_fields = ("name", "description")


@admin.register(GoalContribution)
class GoalContributionAdmin(admin.ModelAdmin):
    """Admin interface for individual goal contributions."""

    list_display = ("goal", "amount", "date", "source")
    list_filter = ("source", "date")
    search_fields = ("goal__name", "notes")
    date_hierarchy = "date"


@admin.register(Debt)
class DebtAdmin(admin.ModelAdmin):
    """Admin interface for tracked debts and repayment progress."""

    list_display = (
        "name",
        "total_amount",
        "borrowed_amount",
        "repaid_amount",
        "repayment_progress_percentage",
        "is_active",
        "created_at",
    )
    list_filter = ("is_active", "created_at")
    search_fields = ("name", "description")
    readonly_fields = ("repaid_amount", "repayment_progress_percentage", "is_fully_repaid")
    fieldsets = (
        (None, {"fields": ("name", "description", "total_amount", "debt_tag")}),
        ("Status", {"fields": ("borrowed_amount", "is_active")}),
    )


@admin.register(DebtTransaction)
class DebtTransactionAdmin(admin.ModelAdmin):
    """Admin interface for individual debt borrowing transactions."""

    list_display = ("debt", "amount", "date", "created_at")
    list_filter = ("date", "created_at")
    search_fields = ("debt__name", "notes")
    date_hierarchy = "date"
