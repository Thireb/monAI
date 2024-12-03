from django.contrib import admin
from .models import Budget, Expense

@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ('month', 'created_at')
    list_filter = ('month',)

@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('name', 'amount', 'budget', 'is_recurring')
    list_filter = ('is_recurring', 'budget__month')
    search_fields = ('name',) 