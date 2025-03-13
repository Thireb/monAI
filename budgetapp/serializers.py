from rest_framework import serializers

from .models import Budget, Expense, SubExpense


class SubExpenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubExpense
        fields = ["id", "name", "amount", "created_at", "updated_at"]


class ExpenseSerializer(serializers.ModelSerializer):
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

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than zero")
        return value


class BudgetSerializer(serializers.ModelSerializer):
    expenses = ExpenseSerializer(many=True, read_only=True)
    month = serializers.DateField(format="%Y-%m")
    total_expenses = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
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
            "remaining_budget",
        ]

    def validate_income(self, value):
        if value < 0:
            raise serializers.ValidationError("Income cannot be negative")
        return value

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["total_expenses"] = sum(expense.amount for expense in instance.expenses.all())
        return data
