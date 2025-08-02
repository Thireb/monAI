from django import forms

from budgetapp.models import Debt, DebtTransaction


class DebtForm(forms.ModelForm):
    """Form for creating and editing debts."""

    class Meta:
        model = Debt
        fields = ["name", "description", "total_amount"]
        widgets = {
            "name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Enter debt name"}
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Describe the debt (e.g., borrowed from friend for motherboard)",
                }
            ),
            "total_amount": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.01",
                    "min": "0.01",
                    "placeholder": "0.00",
                }
            ),
        }

    def clean_total_amount(self):
        total_amount = self.cleaned_data.get("total_amount")
        if total_amount and total_amount <= 0:
            raise forms.ValidationError("Total amount must be greater than zero.")
        return total_amount


class DebtTransactionForm(forms.ModelForm):
    """Form for adding borrowing transactions to debts."""

    class Meta:
        model = DebtTransaction
        fields = ["amount", "date", "notes"]
        widgets = {
            "amount": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.01",
                    "min": "0.01",
                    "placeholder": "0.00",
                }
            ),
            "date": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                }
            ),
            "notes": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 2,
                    "placeholder": "Optional notes about this borrowing",
                }
            ),
        }

    def clean_amount(self):
        amount = self.cleaned_data.get("amount")
        if amount and amount <= 0:
            raise forms.ValidationError("Amount must be greater than zero.")
        return amount
