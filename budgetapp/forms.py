from django import forms
from .models import Expense, SubExpense, Category
from decimal import Decimal

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description', 'icon', 'color']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Category Name'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Category Description'
            }),
            'icon': forms.Select(attrs={
                'class': 'form-control',
            }, choices=[
                ('fa-home', 'Home'),
                ('fa-car', 'Car'),
                ('fa-utensils', 'Food'),
                ('fa-shopping-cart', 'Shopping'),
                ('fa-medical-kit', 'Medical'),
                ('fa-graduation-cap', 'Education'),
                ('fa-plane', 'Travel'),
                ('fa-gamepad', 'Entertainment'),
                ('fa-gift', 'Gift'),
            ]),
            'color': forms.TextInput(attrs={
                'class': 'form-control',
                'type': 'color',
                'data-pickr': 'true'
            }),
        }

class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ['name', 'amount', 'category', 'is_recurring']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'is_recurring': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_amount(self):
        amount = self.cleaned_data['amount']
        if amount <= 0:
            raise forms.ValidationError("Amount must be greater than zero")
        return amount

class SubExpenseForm(forms.ModelForm):
    class Meta:
        model = SubExpense
        fields = ['name', 'amount']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        } 