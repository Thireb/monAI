from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from django.contrib import messages
from .models import Budget, Expense, SubExpense, BudgetLog, ArchivedBudget
from .forms import ExpenseForm, SubExpenseForm
import calendar
from decimal import Decimal
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.db.models import Q

class HomeView(ListView):
    model = Budget
    template_name = 'budgetapp/home.html'
    context_object_name = 'budgets'
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        current_date = timezone.now().date().replace(day=1)
        
        # Get existing budgets
        budgets = Budget.objects.all().order_by('-month')
        context['budgets'] = budgets

        # Get next month for create button
        existing_months = set(budget.month for budget in budgets)
        next_month = current_date
        while next_month in existing_months:
            next_month = (next_month + relativedelta(months=1)).replace(day=1)
        context['next_month'] = next_month

        # Get logs only for existing budgets
        context['budget_logs'] = BudgetLog.objects.filter(
            month__in=existing_months
        ).order_by('-timestamp')
        
        # Paginate budget logs
        logs = BudgetLog.objects.filter(
            month__in=existing_months
        ).order_by('-timestamp')
        paginator = Paginator(logs, 5)
        page = self.request.GET.get('page')
        context['budget_logs'] = paginator.get_page(page)
        
        return context

def create_next_budget(request):
    if request.method == 'POST':
        last_budget = Budget.objects.order_by('-month').first()
        if last_budget:
            next_month = (last_budget.month + relativedelta(months=1)).replace(day=1)
        else:
            next_month = timezone.now().date().replace(day=1)

        # Create new budget
        budget = Budget.objects.create(month=next_month)
        
        # Log the creation
        BudgetLog.objects.create(
            month=budget.month,
            action='create',
            details=f"Budget for {budget.month.strftime('%B %Y')} was created"
        )

        # Copy recurring expenses from previous month if it exists
        if last_budget:
            recurring_expenses = last_budget.expenses.filter(is_recurring=True)
            for expense in recurring_expenses:
                Expense.objects.create(
                    budget=budget,
                    name=expense.name,
                    amount=expense.amount,
                    is_recurring=True
                )
            
        messages.success(request, f'Budget for {next_month.strftime("%B %Y")} has been created!')
        return redirect('home')
    
    return redirect('home')

def budget_detail(request, year, month):
    budget_date = timezone.datetime(year=year, month=month, day=1).date()
    budget = get_object_or_404(Budget, month=budget_date)
    
    if request.method == 'POST':
        form_type = request.POST.get('form_type')
        
        if form_type == 'income':
            income = request.POST.get('income')
            currency = request.POST.get('currency')
            if income:
                budget.income = income
                budget.currency = currency
                budget.save()
        elif form_type == 'expense':
            expense_id = request.POST.get('expense_id')
            if expense_id:  # Edit existing expense
                expense = get_object_or_404(Expense, id=expense_id, budget=budget)
                form = ExpenseForm(request.POST, instance=expense)
            else:  # New expense
                form = ExpenseForm(request.POST)
            
            if form.is_valid():
                expense = form.save(commit=False)
                expense.budget = budget
                expense.save()
        elif form_type == 'delete_expense':
            expense_id = request.POST.get('expense_id')
            if expense_id:
                expense = get_object_or_404(Expense, id=expense_id, budget=budget)
                expense.delete()
        
        return redirect('budget_detail', year=year, month=month)
    else:
        form = ExpenseForm()

    # Calculate total expenses using the model's method
    total_expenses = sum(expense.amount for expense in budget.expenses.all())

    return render(request, 'budgetapp/budget_detail.html', {
        'budget': budget,
        'form': form,
        'expenses': budget.expenses.all(),
        'currency_choices': Budget.get_currency_choices(),
        'total_expenses': total_expenses,
    }) 

def expense_detail(request, expense_id):
    expense = get_object_or_404(Expense, id=expense_id)
    
    if request.method == 'POST':
        form_type = request.POST.get('form_type')
        
        if form_type == 'sub_expense':
            form = SubExpenseForm(request.POST)
            if form.is_valid():
                sub_expense = form.save(commit=False)
                sub_expense.expense = expense
                # Validate that sub_expense amount doesn't exceed remaining amount
                if sub_expense.amount <= expense.get_remaining_amount():
                    sub_expense.save()
        elif form_type == 'edit_sub_expense':
            sub_expense_id = request.POST.get('sub_expense_id')
            if sub_expense_id:
                sub_expense = get_object_or_404(SubExpense, id=sub_expense_id, expense=expense)
                # Calculate the maximum allowed amount for this edit
                max_amount = expense.get_remaining_amount() + sub_expense.amount
                new_amount = Decimal(request.POST.get('amount', 0))
                
                if new_amount <= max_amount:
                    sub_expense.name = request.POST.get('name')
                    sub_expense.amount = new_amount
                    sub_expense.save()
        elif form_type == 'delete_sub_expense':
            sub_expense_id = request.POST.get('sub_expense_id')
            if sub_expense_id:
                sub_expense = get_object_or_404(SubExpense, id=sub_expense_id, expense=expense)
                sub_expense.delete()
        
        return redirect('expense_detail', expense_id=expense_id)
    else:
        form = SubExpenseForm()

    return render(request, 'budgetapp/expense_detail.html', {
        'expense': expense,
        'form': form,
        'sub_expenses': expense.sub_expenses.all(),
    }) 

@require_POST
def delete_budget(request, year_month):
    try:
        year, month = map(int, year_month.split('-'))
        budget = get_object_or_404(Budget, month__year=year, month__month=month)
        # Log the deletion before deleting the budget
        BudgetLog.objects.create(
            month=budget.month,
            action='delete',
            details=f"Budget for {budget.month.strftime('%B %Y')} was deleted"
        )
        budget.delete()
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

def get_next_month(request):
    current_date = timezone.now().date().replace(day=1)
    last_budget = Budget.objects.order_by('-month').first()
    
    if last_budget:
        next_month = (last_budget.month + relativedelta(months=1)).replace(day=1)
    else:
        next_month = current_date
        
    return JsonResponse({
        'next_month': next_month.strftime('%B %Y')
    })

def archive_budget(request, year_month):
    if request.method == 'POST':
        year, month = year_month.split('-')
        budget = get_object_or_404(Budget, year=year, month=month)
        
        # Create archive entry
        ArchivedBudget.objects.create(budget=budget)
        
        messages.success(request, f'Budget for {year}-{month} has been archived')
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)

def view_archives(request):
    archived_budgets = ArchivedBudget.objects.all().select_related('budget')
    
    # Group archives by year
    archives_by_year = {}
    for archive in archived_budgets:
        year = archive.budget.year
        if year not in archives_by_year:
            archives_by_year[year] = []
        archives_by_year[year].append(archive)
    
    context = {
        'archives_by_year': archives_by_year
    }
    return render(request, 'budgetapp/archives.html', context)