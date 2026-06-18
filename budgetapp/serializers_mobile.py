"""Serializers and helpers for mobile offline sync wire formats."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from django.contrib.auth.models import AbstractBaseUser
from django.utils.text import slugify
from rest_framework import serializers

from budgetapp.models import BillReminder, Budget, Category, Expense, SubExpense, Tag


class MobileBudgetSyncSerializer(serializers.ModelSerializer):
    """Wire format for mobile budget pull/push (no nested expenses in v1)."""

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

    def validate_income(self, value: Decimal) -> Decimal:
        """Ensure income is not negative."""
        if value < 0:
            raise serializers.ValidationError("Income cannot be negative")
        return value


class MobileBudgetPushItemSerializer(serializers.Serializer):
    """Single budget item in a mobile push payload."""

    id = serializers.IntegerField(required=False, allow_null=True)
    month = serializers.DateField()
    income = serializers.DecimalField(max_digits=10, decimal_places=2)
    currency = serializers.CharField(max_length=3)
    is_archived = serializers.BooleanField(required=False, default=False)

    def validate_income(self, value: Decimal) -> Decimal:
        """Ensure income is not negative."""
        if value < Decimal("0"):
            raise serializers.ValidationError("Income cannot be negative")
        return value


class MobileCategorySyncSerializer(serializers.ModelSerializer):
    """Wire format for category pull responses."""

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
    """Single category item in a mobile push payload."""

    id = serializers.IntegerField(required=False, allow_null=True)
    name = serializers.CharField(max_length=100)
    description = serializers.CharField(required=False, allow_blank=True, default="")
    icon = serializers.CharField(required=False, allow_blank=True, default="")
    color = serializers.CharField(max_length=7, required=False, default="#000000")

    def validate_name(self, value: str) -> str:
        """Strip whitespace and require a non-empty category name."""
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Name is required")
        return value


class MobileTagSyncSerializer(serializers.ModelSerializer):
    """Wire format for tag pull responses."""

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
    """Single tag item in a mobile push payload."""

    id = serializers.IntegerField(required=False, allow_null=True)
    name = serializers.CharField(max_length=100)
    description = serializers.CharField(required=False, allow_blank=True, default="")
    color = serializers.CharField(max_length=7, required=False, default="#2196f3")
    is_active = serializers.BooleanField(required=False, default=True)

    def validate_name(self, value: str) -> str:
        """Strip whitespace and require a non-empty tag name."""
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Name is required")
        return value


class MobileExpenseSyncSerializer(serializers.ModelSerializer):
    """Wire format for expense pull responses."""

    budget_id = serializers.IntegerField(read_only=True)
    category_id = serializers.IntegerField(read_only=True, allow_null=True)
    tag_id = serializers.IntegerField(source="tag_foreign_key_id", read_only=True, allow_null=True)
    bill_reminder_id = serializers.IntegerField(read_only=True, allow_null=True)

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
            "bill_reminder_id",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class MobileExpensePushItemSerializer(serializers.Serializer):
    """Single expense item in a mobile push payload."""

    id = serializers.IntegerField(required=False, allow_null=True)
    budget_id = serializers.IntegerField(required=False, allow_null=True)
    name = serializers.CharField(max_length=200, required=False, allow_blank=True, default="")
    amount = serializers.DecimalField(
        max_digits=10, decimal_places=2, required=False, allow_null=True
    )
    is_recurring = serializers.BooleanField(required=False, default=False)
    category_id = serializers.IntegerField(required=False, allow_null=True)
    tag_id = serializers.IntegerField(required=False, allow_null=True)
    bill_reminder_id = serializers.IntegerField(required=False, allow_null=True)
    deleted = serializers.BooleanField(required=False, default=False)

    def validate_amount(self, value: Decimal | None) -> Decimal | None:
        """Ensure amount is positive when provided."""
        if value is None:
            return value
        if value <= Decimal("0"):
            raise serializers.ValidationError("Amount must be greater than zero")
        return value

    def validate_name(self, value: str) -> str:
        """Normalize expense name whitespace."""
        return (value or "").strip()

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        """Validate create/update vs delete semantics."""
        if attrs.get("deleted"):
            if attrs.get("id") is None:
                raise serializers.ValidationError({"id": "Required when deleting an expense."})
            return attrs
        budget_id = attrs.get("budget_id")
        if budget_id is None:
            raise serializers.ValidationError({"budget_id": "This field is required."})
        amount = attrs.get("amount")
        if amount is None:
            raise serializers.ValidationError({"amount": "This field is required."})
        if amount <= Decimal("0"):
            raise serializers.ValidationError({"amount": "Amount must be greater than zero"})
        name = (attrs.get("name") or "").strip()
        if not name:
            raise serializers.ValidationError({"name": "Name is required."})
        attrs["name"] = name
        return attrs


class MobileSubExpenseSyncSerializer(serializers.ModelSerializer):
    """Wire format for sub-expense pull responses."""

    expense_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = SubExpense
        fields = [
            "id",
            "expense_id",
            "name",
            "amount",
            "is_return",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class MobileSubExpensePushItemSerializer(serializers.Serializer):
    """Single sub-expense item in a mobile push payload."""

    id = serializers.IntegerField(required=False, allow_null=True)
    expense_id = serializers.IntegerField(required=False, allow_null=True)
    name = serializers.CharField(max_length=200, required=False, allow_blank=True, default="")
    amount = serializers.DecimalField(
        max_digits=10, decimal_places=2, required=False, allow_null=True
    )
    is_return = serializers.BooleanField(required=False, default=False)
    deleted = serializers.BooleanField(required=False, default=False)

    def validate_amount(self, value: Decimal | None) -> Decimal | None:
        """Ensure amount is positive when provided."""
        if value is None:
            return value
        if value <= Decimal("0"):
            raise serializers.ValidationError("Amount must be greater than zero")
        return value

    def validate_name(self, value: str) -> str:
        """Normalize sub-expense name whitespace."""
        return (value or "").strip()

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        """Validate create/update vs delete semantics."""
        if attrs.get("deleted"):
            if attrs.get("id") is None:
                raise serializers.ValidationError({"id": "Required when deleting a sub-expense."})
            return attrs
        expense_id = attrs.get("expense_id")
        if expense_id is None:
            raise serializers.ValidationError({"expense_id": "This field is required."})
        amount = attrs.get("amount")
        if amount is None:
            raise serializers.ValidationError({"amount": "This field is required."})
        if amount <= Decimal("0"):
            raise serializers.ValidationError({"amount": "Amount must be greater than zero"})
        name = (attrs.get("name") or "").strip()
        if not name:
            raise serializers.ValidationError({"name": "Name is required."})
        attrs["name"] = name
        return attrs


def save_category_for_user(
    user: AbstractBaseUser,
    item: dict[str, Any],
) -> tuple[Category | None, bool]:
    """Create or update a category for the given user.

    Args:
        user: Owner of the category.
        item: Validated push payload fields.

    Returns:
        Tuple of (instance, created). Instance is ``None`` when the id is unknown.
    """
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


def save_tag_for_user(
    user: AbstractBaseUser,
    item: dict[str, Any],
) -> tuple[Tag | None, bool]:
    """Create or update a tag for the given user.

    Args:
        user: Owner of the tag.
        item: Validated push payload fields.

    Returns:
        Tuple of (instance, created). Instance is ``None`` when the id is unknown.
    """
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


class MobileBillReminderSyncSerializer(serializers.ModelSerializer):
    """Wire format for bill reminder pull responses."""

    category_id = serializers.IntegerField(read_only=True, allow_null=True)
    tag_id = serializers.IntegerField(read_only=True, allow_null=True)

    class Meta:
        model = BillReminder
        fields = [
            "id",
            "name",
            "amount",
            "category_id",
            "tag_id",
            "next_bill_date",
            "remind_days_before",
            "severity",
            "recurrence_months",
            "is_active",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class MobileBillReminderPushItemSerializer(serializers.Serializer):
    """Single bill reminder item in a mobile push payload."""

    id = serializers.IntegerField(required=False, allow_null=True)
    deleted = serializers.BooleanField(required=False, default=False)
    name = serializers.CharField(max_length=200, required=False, allow_blank=True, default="")
    amount = serializers.DecimalField(
        max_digits=10, decimal_places=2, required=False, allow_null=True
    )
    category_id = serializers.IntegerField(required=False, allow_null=True)
    tag_id = serializers.IntegerField(required=False, allow_null=True)
    next_bill_date = serializers.DateField(required=False, allow_null=True)
    remind_days_before = serializers.IntegerField(required=False, default=30)
    severity = serializers.CharField(
        max_length=10, required=False, default=BillReminder.Severity.MEDIUM
    )
    recurrence_months = serializers.IntegerField(required=False, default=12)
    is_active = serializers.BooleanField(required=False, default=True)
    notes = serializers.CharField(required=False, allow_blank=True, default="")

    def validate_amount(self, value: Decimal | None) -> Decimal | None:
        """Ensure amount is not negative when provided."""
        if value is None:
            return value
        if value < Decimal("0"):
            raise serializers.ValidationError("Amount cannot be negative")
        return value

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        """Validate create/update vs delete semantics and normalize fields."""
        if attrs.get("deleted"):
            if attrs.get("id") is None:
                err = {"id": "Required when deleting a bill reminder."}
                raise serializers.ValidationError(err)
            return attrs
        name = (attrs.get("name") or "").strip()
        if not name:
            raise serializers.ValidationError({"name": "Name is required."})
        attrs["name"] = name
        if attrs.get("amount") is None:
            raise serializers.ValidationError({"amount": "This field is required."})
        if attrs.get("next_bill_date") is None:
            raise serializers.ValidationError({"next_bill_date": "This field is required."})
        sev_ok = {c[0] for c in BillReminder.Severity.choices}
        if attrs.get("severity") not in sev_ok:
            attrs["severity"] = BillReminder.Severity.MEDIUM
        attrs["remind_days_before"] = max(1, int(attrs.get("remind_days_before") or 30))
        attrs["recurrence_months"] = max(1, int(attrs.get("recurrence_months") or 12))
        return attrs


def save_bill_reminder_for_user(
    user: AbstractBaseUser,
    item: dict[str, Any],
) -> tuple[BillReminder | None, bool]:
    """Create or update a bill reminder for the given user.

    Args:
        user: Owner of the reminder.
        item: Validated push payload fields.

    Returns:
        Tuple of (instance, created). Instance is ``None`` when the id is unknown.
    """
    rid = item.get("id")
    if rid is None:
        br = BillReminder.objects.create(
            user=user,
            name=item["name"],
            amount=item["amount"],
            category_id=item.get("category_id"),
            tag_id=item.get("tag_id"),
            next_bill_date=item["next_bill_date"],
            remind_days_before=item.get("remind_days_before", 30),
            severity=item.get("severity", BillReminder.Severity.MEDIUM),
            recurrence_months=item.get("recurrence_months", 12),
            is_active=item.get("is_active", True),
            notes=item.get("notes") or "",
        )
        return br, True
    try:
        br = BillReminder.objects.get(pk=rid, user=user)
    except BillReminder.DoesNotExist:
        return None, False
    br.name = item["name"]
    br.amount = item["amount"]
    br.category_id = item.get("category_id")
    br.tag_id = item.get("tag_id")
    br.next_bill_date = item["next_bill_date"]
    br.remind_days_before = item.get("remind_days_before", 30)
    br.severity = item.get("severity", BillReminder.Severity.MEDIUM)
    br.recurrence_months = item.get("recurrence_months", 12)
    br.is_active = item.get("is_active", True)
    br.notes = item.get("notes") or ""
    br.save()
    return br, False
