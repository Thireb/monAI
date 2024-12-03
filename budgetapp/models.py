from django.db import models
from django.utils import timezone
from decimal import Decimal
from django.contrib.auth import get_user_model
from typing import Optional
from django.core.cache import cache

class Budget(models.Model):
    """
    Represents a monthly budget with income and expenses.
    """
    month: models.DateField = models.DateField()
    income: models.DecimalField = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    currency: models.CharField = models.CharField(max_length=3, default='PKR')
    created_at: models.DateTimeField = models.DateTimeField(auto_now_add=True)
    updated_at: models.DateTimeField = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-month']
        verbose_name_plural = 'Budgets'
        indexes = [
            models.Index(fields=['-month']),
        ]

    def __str__(self):
        return self.month.strftime("%B %Y")

    def was_edited(self):
        """Return True if the budget was edited after creation"""
        return self.updated_at > self.created_at

    def get_remaining_budget(self) -> Decimal:
        """Calculate remaining budget with caching."""
        cache_key = f'budget_remaining_{self.id}'
        cached_value = cache.get(cache_key)
        if cached_value is not None:
            return cached_value

        total_expenses = self.expenses.aggregate(
            total=models.Sum('amount'))['total'] or Decimal('0')
        remaining = self.income - total_expenses
        
        cache.set(cache_key, remaining, timeout=3600)  # Cache for 1 hour
        return remaining

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

    def get_remaining_amount(self):
        total_sub_expenses = self.sub_expenses.aggregate(
            total=models.Sum('amount'))['total'] or Decimal('0')
        return self.amount - total_sub_expenses

class SubExpense(models.Model):
    expense = models.ForeignKey(Expense, on_delete=models.CASCADE, related_name='sub_expenses')
    name = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.amount}"

class BudgetLog(models.Model):
    ACTIONS = (
        ('create', 'Created'),
        ('update', 'Updated'),
        ('delete', 'Deleted'),
    )
    
    month = models.DateField()
    action = models.CharField(max_length=10, choices=ACTIONS)
    timestamp = models.DateTimeField(auto_now_add=True)
    details = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.get_action_display()} - {self.month.strftime('%B %Y')}" 