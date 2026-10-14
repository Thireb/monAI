"""Forms for the new UI."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from django import forms
from django.contrib.auth.models import AbstractBaseUser
from django.utils import timezone

from budgetapp.models import Category, Debt, Expense, Goal, Tag


class LineForm(forms.ModelForm):
    """Add an expense line to a month. Category and account lists hold the user's own only."""

    class Meta:
        model = Expense
        fields = ["name", "amount", "category", "tag_foreign_key", "is_daily", "is_recurring"]
        labels = {
            "name": "Line name",
            "amount": "Amount",
            "tag_foreign_key": "Account",
            "is_daily": "Day-to-day spending",
            "is_recurring": "Repeat every month",
        }

    def __init__(self, *args: Any, user: AbstractBaseUser, **kwargs: Any) -> None:
        """Limit the category and account choices to ``user``."""
        super().__init__(*args, **kwargs)
        self.fields["category"].queryset = Category.objects.filter(user=user).order_by("name")
        self.fields["tag_foreign_key"].queryset = Tag.objects.filter(
            user=user, is_active=True
        ).order_by("name")
        self.fields["category"].empty_label = "No category"
        self.fields["tag_foreign_key"].empty_label = "No account"
        self.fields["category"].required = False
        self.fields["tag_foreign_key"].required = False
        self.fields["amount"].min_value = Decimal("0")
        self.fields["amount"].widget.attrs.update({"inputmode": "decimal", "min": "0"})
        self.fields["name"].widget.attrs.update({"autocomplete": "off"})

    def clean_amount(self) -> Decimal:
        """The amount cannot be negative."""
        amount = self.cleaned_data["amount"]
        if amount < 0:
            raise forms.ValidationError("The amount cannot be negative.")
        return amount


class GoalForm(forms.ModelForm):
    """Start a savings goal. ``saved`` is an optional amount that is already saved."""

    saved = forms.DecimalField(
        label="Already saved (optional)",
        required=False,
        min_value=Decimal("0"),
        max_digits=10,
        decimal_places=2,
    )

    class Meta:
        model = Goal
        fields = ["name", "target_amount", "target_date"]
        labels = {
            "name": "Goal name",
            "target_amount": "Target amount",
            "target_date": "Reach it by (optional)",
        }
        widgets = {"target_date": forms.DateInput(attrs={"type": "date"})}

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Set the input hints."""
        super().__init__(*args, **kwargs)
        for name in ("target_amount", "saved"):
            self.fields[name].widget.attrs.update({"inputmode": "decimal", "min": "0"})
        self.fields["name"].widget.attrs.update({"autocomplete": "off"})

    def clean(self) -> dict[str, Any]:
        """The target must be above 0, in the future, and not below the saved amount."""
        cleaned = super().clean() or {}
        target = cleaned.get("target_amount")
        saved = cleaned.get("saved")
        target_date = cleaned.get("target_date")
        if target is not None and target <= 0:
            self.add_error("target_amount", "The target must be more than 0.")
        if target and saved and saved > target:
            self.add_error("saved", "The saved amount cannot be more than the target.")
        if target_date and target_date <= timezone.localdate():
            self.add_error("target_date", "Pick a date in the future.")
        return cleaned


class DebtForm(forms.ModelForm):
    """Add a debt. ``borrowed`` is an optional amount that is already borrowed."""

    borrowed = forms.DecimalField(
        label="Borrowed so far (optional)",
        required=False,
        min_value=Decimal("0"),
        max_digits=10,
        decimal_places=2,
    )

    class Meta:
        model = Debt
        fields = ["name", "total_amount"]
        labels = {"name": "Debt name", "total_amount": "Most you may borrow"}

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Set the input hints."""
        super().__init__(*args, **kwargs)
        for name in ("total_amount", "borrowed"):
            self.fields[name].widget.attrs.update({"inputmode": "decimal", "min": "0"})
        self.fields["name"].widget.attrs.update({"autocomplete": "off"})

    def clean(self) -> dict[str, Any]:
        """The limit must be above 0 and not below the borrowed amount."""
        cleaned = super().clean() or {}
        limit = cleaned.get("total_amount")
        borrowed = cleaned.get("borrowed")
        if limit is not None and limit <= 0:
            self.add_error("total_amount", "The amount must be more than 0.")
        if limit and borrowed and borrowed > limit:
            self.add_error("borrowed", "This is more than the most you may borrow.")
        return cleaned
