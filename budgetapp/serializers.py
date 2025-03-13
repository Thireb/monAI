from rest_framework import serializers

from .models import Budget, Expense, Goal, GoalContribution, SubExpense


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


class GoalContributionSerializer(serializers.ModelSerializer):
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

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Contribution amount must be greater than zero")
        return value


class GoalSerializer(serializers.ModelSerializer):
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
        read_only_fields = ["user", "progress_percentage"]

    def validate(self, data):
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

    def create(self, validated_data):
        # Set the user from the request
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Get the progress percentage
        data["progress_percentage"] = instance.progress_percentage
        # Get on track status
        data["is_on_track"] = instance.is_on_track()
        # Get monthly contribution needed
        data["monthly_contribution_needed"] = instance.monthly_contribution_needed()
        return data


class GoalDetailSerializer(GoalSerializer):
    """Serializer for detailed goal view with recent contributions."""

    recent_contributions = serializers.SerializerMethodField()

    class Meta(GoalSerializer.Meta):
        fields = GoalSerializer.Meta.fields + ["recent_contributions"]

    def get_recent_contributions(self, instance):
        """Get the 5 most recent contributions."""
        contributions = instance.contributions.all().order_by("-date")[:5]
        return GoalContributionSerializer(contributions, many=True).data
