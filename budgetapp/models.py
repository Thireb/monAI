from django.db import models
from django.utils import timezone
from decimal import Decimal

class Budget(models.Model):
    month = models.DateField()
    income = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, default='PKR')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-month']

    def __str__(self):
        return self.month.strftime("%B %Y")

    def get_remaining_budget(self):
        total_expenses = self.expenses.aggregate(
            total=models.Sum('amount'))['total'] or Decimal('0')
        return self.income - total_expenses

    @staticmethod
    def get_currency_choices():
        # Common currencies with their names
        currencies = [
            ('PKR', 'PKR - Pakistani Rupee'),
            ('USD', 'USD - US Dollar'),
            ('EUR', 'EUR - Euro'),
            ('GBP', 'GBP - British Pound'),
            ('AUD', 'AUD - Australian Dollar'),
            ('CAD', 'CAD - Canadian Dollar'),
            ('JPY', 'JPY - Japanese Yen'),
            ('CNY', 'CNY - Chinese Yuan'),
            ('INR', 'INR - Indian Rupee'),
            ('AED', 'AED - UAE Dirham'),
            ('SAR', 'SAR - Saudi Riyal'),
        ]
        return currencies

class Expense(models.Model):
    budget = models.ForeignKey(Budget, on_delete=models.CASCADE, related_name='expenses')
    name = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    is_recurring = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.amount}" 