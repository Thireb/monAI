"""Forms for the new UI."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from django import forms
from django.contrib.auth.models import AbstractBaseUser

from budgetapp.models import Category, Expense, Tag


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
