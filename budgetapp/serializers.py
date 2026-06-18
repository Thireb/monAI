"""DRF serializers for budgets, expenses, and goals."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from rest_framework import serializers

from .models import Budget, Expense, Goal, GoalContribution, SubExpense


class SubExpenseSerializer(serializers.ModelSerializer):
    """Read/write serializer for sub-expense line items."""

    class Meta:
        model = SubExpense
        fields = ["id", "name", "amount", "created_at", "updated_at"]


class ExpenseSerializer(serializers.ModelSerializer):
    """Serializer for expense line items with nested sub-expenses."""

    sub_expenses = SubExpenseSerializer(many=True, read_only=True)
    remaining_amount = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = Expense
        fields = [
            "id",
            "name",
            "amount",
            "is_recurring",
            "created_at",
            "updated_at",
            "sub_expenses",
            "remaining_amount",
        ]

    def validate_amount(self, value: Decimal) -> Decimal:
        """Ensure expense amount is positive."""
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than zero")
        return value


class BudgetSerializer(serializers.ModelSerializer):
    """Serializer for monthly budgets with computed expense totals."""

    expenses = ExpenseSerializer(many=True, read_only=True)
    month = serializers.DateField(format="%Y-%m")
    total_expenses = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    total_returns = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    net_expenses = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    remaining_budget = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True, source="get_remaining_budget"
    )

    class Meta:
        model = Budget
        fields = [
            "id",
            "month",
            "income",
            "currency",
            "created_at",
            "updated_at",
            "expenses",
            "total_expenses",
            "total_returns",
            "net_expenses",
            "remaining_budget",
        ]

    def validate_income(self, value: Decimal) -> Decimal:
        """Ensure income is not negative."""
        if value < 0:
            raise serializers.ValidationError("Income cannot be negative")
        return value

    def to_representation(self, instance: Budget) -> dict[str, Any]:
        """Add computed expense totals to the serialized output."""
        data = super().to_representation(instance)
        data["total_expenses"] = instance.get_gross_budgeted_expenses()
        data["total_returns"] = instance.get_total_returns()
        data["net_expenses"] = instance.get_net_budgeted_expenses()
        return data


class GoalContributionSerializer(serializers.ModelSerializer):
    """Serializer for individual goal contributions."""

    class Meta:
        model = GoalContribution
        fields = [
            "id",
            "goal",
            "amount",
            "date",
            "source",
            "notes",
        ]

    def validate_amount(self, value: Decimal) -> Decimal:
        """Ensure contribution amount is positive."""
        if value <= 0:
            raise serializers.ValidationError("Contribution amount must be greater than zero")
        return value


class GoalSerializer(serializers.ModelSerializer):
    """Serializer for savings goals with computed progress fields."""

    progress_percentage = serializers.IntegerField(read_only=True)
    is_on_track = serializers.BooleanField(read_only=True)
    monthly_contribution_needed = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True
    )

    class Meta:
        model = Goal
        fields = [
            "id",
            "user",
            "name",
            "description",
            "target_amount",
            "current_amount",
            "start_date",
            "target_date",
            "category",
            "is_active",
            "progress_percentage",
            "is_on_track",
            "monthly_contribution_needed",
        ]
        read_only_fields = ["progress_percentage"]

    def validate(self, data: dict[str, Any]) -> dict[str, Any]:
        """Validate goal amounts and date ordering."""
        if "target_amount" in data and data["target_amount"] <= 0:
            raise serializers.ValidationError(
                {"target_amount": "Target amount must be greater than zero"}
            )

        if "current_amount" in data and data["current_amount"] < 0:
            raise serializers.ValidationError(
                {"current_amount": "Current amount cannot be negative"}
            )

        if (
            "target_date" in data
            and "start_date" in data
            and data["target_date"] <= data["start_date"]
        ):
            raise serializers.ValidationError(
                {"target_date": "Target date must be after start date"}
            )

        return data

    def to_representation(self, instance: Goal) -> dict[str, Any]:
        """Attach computed progress and tracking fields."""
        data = super().to_representation(instance)
        data["progress_percentage"] = instance.progress_percentage
        data["is_on_track"] = instance.is_on_track()
        data["monthly_contribution_needed"] = instance.monthly_contribution_needed()
        return data


class GoalDetailSerializer(GoalSerializer):
    """Extended goal serializer including recent contributions."""

    recent_contributions = serializers.SerializerMethodField()

    class Meta(GoalSerializer.Meta):
        fields = GoalSerializer.Meta.fields + ["recent_contributions"]

    def get_recent_contributions(self, instance: Goal) -> Any:
        """Return the five most recent contributions for the goal."""
        contributions = instance.contributions.all().order_by("-date")[:5]
        return GoalContributionSerializer(contributions, many=True).data
