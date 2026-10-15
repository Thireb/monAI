"""Forms for the new UI."""

from __future__ import annotations

import re
import uuid
from decimal import Decimal
from typing import Any

from django import forms
from django.contrib.auth.models import AbstractBaseUser
from django.core.validators import MinValueValidator
from django.utils import timezone
from django.utils.text import slugify

from budgetapp.models import (
    BillReminder,
    Budget,
    Category,
    Debt,
    Expense,
    Goal,
    Tag,
    TagTransfer,
)


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


class NamedForm(forms.ModelForm):
    """Base for a user's account or category: the name and its slug are unique per user.

    The slug follows the name, so a renamed item frees its old slug. A name without Latin
    letters or digits gets a random slug.
    """

    slug_prefix = "item"

    def __init__(self, *args: Any, user: AbstractBaseUser, **kwargs: Any) -> None:
        """Keep the owner for the checks and for ``save``."""
        super().__init__(*args, **kwargs)
        self.user = user
        self.slug = ""
        self.fields["name"].widget.attrs.update({"autocomplete": "off"})
        self.fields["color"].widget = forms.TextInput(attrs={"type": "color"})

    def clean_name(self) -> str:
        """Refuse a name (or slug) that another item of the user has."""
        name = self.cleaned_data["name"].strip()
        others = type(self.instance).objects.filter(user=self.user).exclude(pk=self.instance.pk)
        if others.filter(name__iexact=name).exists():
            raise forms.ValidationError("You already have one with this name.")
        self.slug = slugify(name)[:90] or f"{self.slug_prefix}-{uuid.uuid4().hex[:8]}"
        if others.filter(slug=self.slug).exists():
            raise forms.ValidationError("This name is too close to one you already have.")
        return name

    def clean_color(self) -> str:
        """The colour must be a hex code like #2e8b57."""
        color = self.cleaned_data["color"]
        if not re.fullmatch(r"#[0-9a-fA-F]{6}", color or ""):
            raise forms.ValidationError("Pick a colour.")
        return color

    def save(self, commit: bool = True) -> Any:
        """Set the owner and the slug, then save."""
        item = super().save(commit=False)
        item.user = self.user
        item.slug = self.slug
        if commit:
            item.save()
        return item


class AccountForm(NamedForm):
    """Add or edit an account (a ``Tag``)."""

    slug_prefix = "account"

    class Meta:
        model = Tag
        fields = ["name", "color", "is_active"]
        labels = {"name": "Account name", "color": "Colour", "is_active": "Use for new lines"}


class CategoryForm(NamedForm):
    """Add or edit a category."""

    slug_prefix = "category"

    class Meta:
        model = Category
        fields = ["name", "color"]
        labels = {"name": "Category name", "color": "Colour"}


class BillForm(forms.ModelForm):
    """Add or edit a bill reminder. Category and account lists hold the user's own only."""

    class Meta:
        model = BillReminder
        fields = [
            "name",
            "amount",
            "next_bill_date",
            "recurrence_months",
            "remind_days_before",
            "category",
            "tag",
            "is_active",
        ]
        labels = {
            "name": "Bill name",
            "next_bill_date": "Next due date",
            "recurrence_months": "Repeats every (months)",
            "remind_days_before": "Remind me (days before)",
            "tag": "Account",
            "is_active": "Active",
        }
        widgets = {"next_bill_date": forms.DateInput(attrs={"type": "date"})}
        help_texts = {"recurrence_months": "", "remind_days_before": ""}

    def __init__(self, *args: Any, user: AbstractBaseUser, **kwargs: Any) -> None:
        """Limit the choices to ``user`` and set the input hints."""
        super().__init__(*args, **kwargs)
        self.user = user
        self.fields["category"].queryset = Category.objects.filter(user=user).order_by("name")
        self.fields["tag"].queryset = Tag.objects.filter(user=user).order_by("name")
        self.fields["category"].empty_label = "No category"
        self.fields["tag"].empty_label = "No account"
        self.fields["amount"].widget.attrs.update({"inputmode": "decimal", "min": "0"})
        for name in ("recurrence_months", "remind_days_before"):
            self.fields[name].validators.append(MinValueValidator(1))
            self.fields[name].widget.attrs["min"] = "1"
        self.fields["name"].widget.attrs.update({"autocomplete": "off"})

    def clean_amount(self) -> Decimal:
        """The amount cannot be negative."""
        amount = self.cleaned_data["amount"]
        if amount < 0:
            raise forms.ValidationError("The amount cannot be negative.")
        return amount

    def save(self, commit: bool = True) -> Any:
        """Set the owner, then save."""
        bill = super().save(commit=False)
        bill.user = self.user
        if commit:
            bill.save()
        return bill


class IncomeForm(forms.ModelForm):
    """Change a month's income and currency."""

    class Meta:
        model = Budget
        fields = ["income", "currency"]
        labels = {"income": "Income this month", "currency": "Currency"}

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Offer the common currencies, and the month's own if it is not one of them."""
        super().__init__(*args, **kwargs)
        choices = list(Budget.get_currency_choices())
        current = self.instance.currency if self.instance else ""
        if current and current not in {code for code, _ in choices}:
            choices.insert(0, (current, current))
        self.fields["currency"].widget = forms.Select(choices=choices)
        self.currency_codes = {code for code, _ in choices}
        self.fields["income"].widget.attrs.update({"inputmode": "decimal", "min": "0"})

    def clean_income(self) -> Decimal:
        """The income cannot be negative."""
        income = self.cleaned_data["income"]
        if income < 0:
            raise forms.ValidationError("The income cannot be negative.")
        return income

    def clean_currency(self) -> str:
        """The currency must be one of the choices."""
        currency = self.cleaned_data["currency"]
        if currency not in self.currency_codes:
            raise forms.ValidationError("Pick a currency from the list.")
        return currency


class TransferForm(forms.ModelForm):
    """Move money between 2 accounts in a month. The model checks the rules on save."""

    class Meta:
        model = TagTransfer
        fields = ["from_tag", "to_tag", "amount", "note"]
        labels = {"from_tag": "From account", "to_tag": "To account", "note": "Note (optional)"}

    def __init__(self, *args: Any, user: AbstractBaseUser, **kwargs: Any) -> None:
        """Limit both account lists to the user's active accounts."""
        super().__init__(*args, **kwargs)
        accounts = Tag.objects.filter(user=user, is_active=True).order_by("name")
        for name in ("from_tag", "to_tag"):
            self.fields[name].queryset = accounts
            self.fields[name].empty_label = "Pick an account"
        self.fields["amount"].widget.attrs.update({"inputmode": "decimal", "min": "0"})
