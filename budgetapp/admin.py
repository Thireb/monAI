from django.contrib import admin

from .models import (
    Budget,
    Debt,
    DebtTransaction,
    Expense,
    Goal,
    GoalContribution,
    Tag,
)


@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ("month", "created_at")
    list_filter = ("month",)


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ("name", "amount", "budget", "is_recurring")
    list_filter = ("is_recurring", "budget__month")
    search_fields = ("name",)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "description", "color", "is_active", "created_at")
    list_filter = ("is_active", "created_at")
    search_fields = ("name", "description")
    readonly_fields = ("created_at", "updated_at")


@admin.register(Goal)
class GoalAdmin(admin.ModelAdmin):
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
    list_display = ("goal", "amount", "date", "source")
    list_filter = ("source", "date")
    search_fields = ("goal__name", "notes")
    date_hierarchy = "date"


@admin.register(Debt)
class DebtAdmin(admin.ModelAdmin):
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
    list_display = ("debt", "amount", "date", "created_at")
    list_filter = ("date", "created_at")
    search_fields = ("debt__name", "notes")
    date_hierarchy = "date"


