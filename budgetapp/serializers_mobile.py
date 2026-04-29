from decimal import Decimal

from rest_framework import serializers

from budgetapp.models import Budget


class MobileBudgetSyncSerializer(serializers.ModelSerializer):
    """Wire format for mobile pull/push (no nested expenses in v1)."""

    month = serializers.DateField(format="%Y-%m-%d")

    class Meta:
        model = Budget
        fields = [
            "id",
            "month",
            "income",
            "currency",
            "is_archived",
            "updated_at",
        ]
        read_only_fields = ["id", "updated_at"]

    def validate_income(self, value):
        if value < 0:
            raise serializers.ValidationError("Income cannot be negative")
        return value


class MobileBudgetPushItemSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=False, allow_null=True)
    month = serializers.DateField()
    income = serializers.DecimalField(max_digits=10, decimal_places=2)
    currency = serializers.CharField(max_length=3)
    is_archived = serializers.BooleanField(required=False, default=False)

    def validate_income(self, value):
        if value < Decimal("0"):
            raise serializers.ValidationError("Income cannot be negative")
        return value
