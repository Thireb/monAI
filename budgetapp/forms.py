from django import forms
from .models import Expense, SubExpense, Category
from decimal import Decimal


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
            "amount": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.01"}
            ),
            "is_return": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }
        labels = {"is_return": "Mark as Return/Refund"}
        help_texts = {
            "is_return": "Check this if this is a return or refund that should be added back to the budget"
        }
