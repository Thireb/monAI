from django import forms
from django.utils import timezone

from .models import Category, Expense, Goal, GoalContribution, SubExpense


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ["name", "description", "icon", "color"]
        widgets = {
            "name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Enter category name"}
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Enter category description",
                }
            ),
            "icon": forms.Select(
                attrs={"class": "form-select"},
                choices=[
                    ("fa-home", "🏠 Home"),
                    ("fa-car", "🚗 Car"),
                    ("fa-utensils", "🍽️ Food"),
                    ("fa-shopping-cart", "🛒 Shopping"),
                    ("fa-medical-kit", "⚕️ Medical"),
                    ("fa-graduation-cap", "🎓 Education"),
                    ("fa-plane", "✈️ Travel"),
                    ("fa-gamepad", "🎮 Entertainment"),
                    ("fa-gift", "🎁 Gift"),
                ],
            ),
            "color": forms.TextInput(
                attrs={"class": "form-control color-picker", "type": "hidden"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["name"].label = "Category Name"
        self.fields["description"].label = "Description"
        self.fields["icon"].label = "Icon"
        self.fields["color"].label = "Color"


class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ["name", "amount", "category", "is_recurring"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "amount": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.01", "min": "0"}
            ),
            "category": forms.Select(attrs={"class": "form-control"}),
            "is_recurring": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def clean_amount(self):
        amount = self.cleaned_data["amount"]
        if amount <= 0:
            raise forms.ValidationError("Amount must be greater than zero")
        return amount


class SubExpenseForm(forms.ModelForm):
    class Meta:
        model = SubExpense
        fields = ["name", "amount", "is_return"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "amount": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "is_return": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }
        labels = {"is_return": "Mark as Return/Refund"}
        help_texts = {
            "is_return": "Check this if this is a return or refund that should be added "
            "back to the budget"
        }


class GoalForm(forms.ModelForm):
    class Meta:
        model = Goal
        fields = [
            "name",
            "description",
            "target_amount",
            "current_amount",
            "start_date",
            "target_date",
            "category",
            "is_active",
        ]
        widgets = {
            "name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Enter goal name"}
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Enter goal description",
                }
            ),
            "target_amount": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.01", "min": "0.01"}
            ),
            "current_amount": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.01", "min": "0"}
            ),
            "start_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "target_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "category": forms.Select(attrs={"class": "form-select"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, **kwargs):
        # Remove user parameter if it exists
        if "user" in kwargs:
            kwargs.pop("user")
        super().__init__(*args, **kwargs)
        self.fields["start_date"].initial = timezone.now().date()

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get("start_date")
        target_date = cleaned_data.get("target_date")
        target_amount = cleaned_data.get("target_amount")
        current_amount = cleaned_data.get("current_amount")

        if target_date and start_date and target_date <= start_date:
            self.add_error("target_date", "Target date must be after start date")

        if target_amount is not None and target_amount <= 0:
            self.add_error("target_amount", "Target amount must be greater than zero")

        if current_amount is not None and current_amount < 0:
            self.add_error("current_amount", "Current amount cannot be negative")

        if current_amount and target_amount and current_amount > target_amount:
            self.add_error("current_amount", "Current amount cannot exceed target amount")

        return cleaned_data


class GoalContributionForm(forms.ModelForm):
    class Meta:
        model = GoalContribution
        fields = ["amount", "date", "source", "notes"]
        widgets = {
            "amount": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.01", "min": "0.01"}
            ),
            "date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "source": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Source of funds"}
            ),
            "notes": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 2,
                    "placeholder": "Optional notes about this contribution",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["date"].initial = timezone.now().date()

    def clean_amount(self):
        amount = self.cleaned_data["amount"]
        if amount <= 0:
            raise forms.ValidationError("Contribution amount must be greater than zero")
        return amount
