from django import forms
from .models import Expense, SubExpense

class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ['name', 'amount', 'is_recurring']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'is_recurring': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        } 

class SubExpenseForm(forms.ModelForm):
    class Meta:
        model = SubExpense
        fields = ['name', 'amount']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        } 