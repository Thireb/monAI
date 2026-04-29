from decimal import Decimal

from django.utils.text import slugify
from rest_framework import serializers

from budgetapp.models import Budget, Category, Expense, Tag


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


class MobileCategorySyncSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "icon",
            "color",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class MobileCategoryPushItemSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=False, allow_null=True)
    name = serializers.CharField(max_length=100)
    description = serializers.CharField(required=False, allow_blank=True, default="")
    icon = serializers.CharField(required=False, allow_blank=True, default="")
    color = serializers.CharField(max_length=7, required=False, default="#000000")

    def validate_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Name is required")
        return value


class MobileTagSyncSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "color",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class MobileTagPushItemSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=False, allow_null=True)
    name = serializers.CharField(max_length=100)
    description = serializers.CharField(required=False, allow_blank=True, default="")
    color = serializers.CharField(max_length=7, required=False, default="#2196f3")
    is_active = serializers.BooleanField(required=False, default=True)

    def validate_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Name is required")
        return value


class MobileExpenseSyncSerializer(serializers.ModelSerializer):
    budget_id = serializers.IntegerField(read_only=True)
    category_id = serializers.IntegerField(read_only=True, allow_null=True)
    tag_id = serializers.IntegerField(source="tag_foreign_key_id", read_only=True, allow_null=True)

    class Meta:
        model = Expense
        fields = [
            "id",
            "budget_id",
            "name",
            "amount",
            "is_recurring",
            "category_id",
            "tag_id",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class MobileExpensePushItemSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=False, allow_null=True)
    budget_id = serializers.IntegerField()
    name = serializers.CharField(max_length=200)
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    is_recurring = serializers.BooleanField(required=False, default=False)
    category_id = serializers.IntegerField(required=False, allow_null=True)
    tag_id = serializers.IntegerField(required=False, allow_null=True)

    def validate_amount(self, value):
        if value <= Decimal("0"):
            raise serializers.ValidationError("Amount must be greater than zero")
        return value

    def validate_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Name is required")
        return value


def save_category_for_user(user, item):
    """Create or update category; returns (instance, created) or (None, False) if id unknown."""
    cid = item.get("id")
    name = item["name"]
    description = item.get("description") or ""
    icon = item.get("icon") or ""
    color = item.get("color") or "#000000"
    slug_base = slugify(name) or "category"
    if cid is None:
        c = Category.objects.create(
            user=user,
            name=name,
            slug=slug_base,
            description=description,
            icon=icon,
            color=color,
        )
        return c, True
    try:
        c = Category.objects.get(pk=cid, user=user)
    except Category.DoesNotExist:
        return None, False
    c.name = name
    c.slug = slug_base
    c.description = description
    c.icon = icon
    c.color = color
    c.save()
    return c, False


def save_tag_for_user(user, item):
    """Create or update tag; returns (instance, created) or (None, False) if id unknown."""
    cid = item.get("id")
    name = item["name"]
    description = item.get("description") or ""
    color = item.get("color") or "#2196f3"
    is_active = item.get("is_active", True)
    slug_base = slugify(name) or "tag"
    if cid is None:
        t = Tag.objects.create(
            user=user,
            name=name,
            slug=slug_base,
            description=description,
            color=color,
            is_active=is_active,
        )
        return t, True
    try:
        t = Tag.objects.get(pk=cid, user=user)
    except Tag.DoesNotExist:
        return None, False
    t.name = name
    t.slug = slug_base
    t.description = description
    t.color = color
    t.is_active = is_active
    t.save()
    return t, False
