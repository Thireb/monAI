from django.contrib import admin

from .models import Budget, Expense, Goal, GoalContribution


@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ("month", "created_at")
    list_filter = ("month",)


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ("name", "amount", "budget", "is_recurring")
    list_filter = ("is_recurring", "budget__month")
    search_fields = ("name",)


@admin.register(Goal)
class GoalAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "user",
        "target_amount",
        "current_amount",
        "progress_percentage",
        "target_date",
        "category",
        "is_active",
    )
    list_filter = ("category", "is_active")
    search_fields = ("name", "description", "user__username")


@admin.register(GoalContribution)
class GoalContributionAdmin(admin.ModelAdmin):
    list_display = ("goal", "amount", "date", "source")
    list_filter = ("source", "date")
    search_fields = ("goal__name", "notes")
    date_hierarchy = "date"
