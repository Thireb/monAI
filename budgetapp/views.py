from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from .models import Budget, Expense
from .forms import ExpenseForm
import calendar

class HomeView(ListView):
    model = Budget
    template_name = 'budgetapp/home.html'
    context_object_name = 'budgets'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get current month and previous 11 months
        current_date = timezone.now().date().replace(day=1)
        months = []
        for i in range(12):
            month_date = current_date - relativedelta(months=i)
            budget, created = Budget.objects.get_or_create(month=month_date)
            if created:
                # Copy recurring expenses from previous month
                prev_month = month_date - relativedelta(months=1)
                prev_budget = Budget.objects.filter(month=prev_month).first()
                if prev_budget:
                    recurring_expenses = prev_budget.expenses.filter(is_recurring=True)
                    for expense in recurring_expenses:
                        Expense.objects.create(
                            budget=budget,
                            name=expense.name,
                            amount=expense.amount,
                            is_recurring=True
                        )
            months.append(budget)
        context['months'] = months
        return context

def budget_detail(request, year, month):
    budget_date = timezone.datetime(year=year, month=month, day=1).date()
    budget = get_object_or_404(Budget, month=budget_date)
    
    if request.method == 'POST':
        form = ExpenseForm(request.POST)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.budget = budget
            expense.save()
            return redirect('budget_detail', year=year, month=month)
    else:
        form = ExpenseForm()

    return render(request, 'budgetapp/budget_detail.html', {
        'budget': budget,
        'form': form,
        'expenses': budget.expenses.all()
    }) 