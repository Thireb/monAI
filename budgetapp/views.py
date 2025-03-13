from datetime import timedelta
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import DecimalField, F, Sum, Value
from django.db.models.functions import Coalesce
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods, require_POST
from django.views.generic import ListView

from dateutil.relativedelta import relativedelta

from .forms import CategoryForm, ExpenseForm, GoalContributionForm, GoalForm, SubExpenseForm
from .models import (
    ArchivedBudget,
    Budget,
    BudgetDeletionLog,
    BudgetLog,
    Category,
    Expense,
    Goal,
    IncomeHistory,
    RecentUpdate,
    SubExpense,
)

TEMPLATE_VERSION = "material"  # or 'budgetapp' for original templates


class HomeView(ListView):
    model = Budget
    template_name = f"{TEMPLATE_VERSION}/home.html"
    context_object_name = "budgets"
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Auto-archive old budgets
        current_date = timezone.now().date()
        old_budgets = Budget.objects.filter(is_archived=False, month__year__lt=current_date.year)

        with transaction.atomic():
            for budget in old_budgets:
                if not ArchivedBudget.objects.filter(budget=budget).exists():
                    ArchivedBudget.objects.create(budget=budget)
                    budget.is_archived = True
                    budget.save()

        # Get active budgets sorted by month
        active_budgets = Budget.objects.filter(is_archived=False).order_by("month")
        first_budget = active_budgets.first()
        last_budget = active_budgets.last()

        if not first_budget:
            # No active budgets, use earliest archived budget's month or system date
            archived_budget = Budget.objects.filter(is_archived=True).order_by("month").first()
            current_date = (
                archived_budget.month if archived_budget else timezone.now().date().replace(day=1)
            )
        else:
            current_date = last_budget.month + relativedelta(months=1)

        # Get existing budgets
        budgets = Budget.objects.filter(is_archived=False).order_by("-month")
        context["budgets"] = budgets

        # Get active deletion logs and clean up expired ones
        BudgetDeletionLog.objects.filter(expires_at__lte=timezone.now()).delete()
        context["deletion_logs"] = BudgetDeletionLog.objects.all()

        # Check if we have an active budget for current month
        has_active_current_month = (
            Budget.objects.filter(
                is_archived=False,
                month__year=current_date.year,
                month__month=current_date.month,
            ).count()
            > 0
        )

        if not has_active_current_month:
            next_month = current_date
        else:
            next_month = (current_date + relativedelta(months=1)).replace(day=1)

        context["next_month"] = next_month

        # Get months for budget logs
        active_budget_months = set(budget.month for budget in budgets)

        # Get logs only for existing budgets
        context["budget_logs"] = BudgetLog.objects.filter(month__in=active_budget_months).order_by(
            "-timestamp"
        )

        # Paginate budget logs
        logs = BudgetLog.objects.filter(month__in=active_budget_months).order_by("-timestamp")
        paginator = Paginator(logs, 5)
        page = self.request.GET.get("page")
        context["budget_logs"] = paginator.get_page(page)

        return context


def create_next_budget(request):
    if request.method == "POST":
        last_budget = Budget.objects.order_by("-month").first()
        if last_budget:
            next_month = (last_budget.month + relativedelta(months=1)).replace(day=1)
        else:
            next_month = timezone.now().date().replace(day=1)

        # Create new budget
        budget = Budget.objects.create(month=next_month)

        # Copy recurring expenses from previous budget if it exists
        if last_budget:
            recurring_expenses = last_budget.expenses.filter(is_recurring=True)
            for expense in recurring_expenses:
                # Create a copy of the recurring expense in the new budget
                Expense.objects.create(
                    budget=budget,
                    name=expense.name,
                    amount=expense.amount,
                    is_recurring=True,
                    category=expense.category,
                )

        # Log the creation
        BudgetLog.objects.create(
            month=budget.month,
            action="create",
            details=f"Budget for {budget.month.strftime('%B %Y')} was created",
        )

        # Clean success message without any special characters
        messages.success(request, f'Budget for {next_month.strftime("%B %Y")} has been created')
        return redirect("home")

    return redirect("home")


@require_http_methods(["GET", "POST"])
def budget_detail(request, year, month):
    budget_date = timezone.datetime(year=year, month=month, day=1).date()
    budget = get_object_or_404(Budget, month=budget_date)

    if request.method == "POST":
        form_type = request.POST.get("form_type")

        if form_type == "income":
            return handle_income_update(request, budget)
        elif form_type == "expense":
            expense_id = request.POST.get("expense_id")
            if expense_id:
                # This is an update
                expense = get_object_or_404(Expense, id=expense_id, budget=budget)
                form = ExpenseForm(request.POST, instance=expense)
            else:
                # This is a new expense
                form = ExpenseForm(request.POST)

            if form.is_valid():
                expense = form.save(commit=False)
                expense.budget = budget
                expense.save()

                if expense_id:
                    messages.success(request, "Expense updated successfully!")
                else:
                    messages.success(request, "Expense added successfully!")
                    # Create a recent update entry
                    RecentUpdate.objects.create(
                        budget=budget,
                        action_type="expense_added",
                        description=(
                            f"Added expense: {expense.name} "
                            f"({budget.currency} {expense.amount})"
                        ),
                        amount=expense.amount,
                        category=expense.category,
                    )

        elif form_type == "delete_expense":
            return handle_expense_delete(request, budget)

        return redirect("budget_detail", year=year, month=month)

    # Get expenses with related categories in a single query
    expenses = (
        budget.expenses.select_related("category")
        .prefetch_related("sub_expenses", "category")
        .order_by("-created_at")
    )

    # Calculate totals using database aggregation
    total_expenses = expenses.aggregate(
        total=Coalesce(Sum("amount"), Value(0), output_field=DecimalField())
    )["total"]

    # Calculate category statistics
    expenses_by_category = calculate_category_stats(expenses, total_expenses)

    context = {
        "budget": budget,
        "form": ExpenseForm(),
        "expenses": expenses,
        "currency_choices": Budget.get_currency_choices(),
        "total_expenses": total_expenses,
        "expenses_by_category": expenses_by_category,
        "categories": Category.objects.all(),
        "income_history": IncomeHistory.objects.filter(budget=budget)[:5],
    }

    return render(request, f"{TEMPLATE_VERSION}/budget_detail.html", context)


def calculate_category_stats(expenses, total_expenses):
    stats = {}
    for expense in expenses:
        category_name = expense.category.name if expense.category else "Uncategorized"
        if category_name not in stats:
            stats[category_name] = {
                "amount": Decimal("0"),
                "color": expense.category.color if expense.category else "#95A5A6",
                "icon": (expense.category.icon if expense.category else "fa-question-circle"),
            }
        stats[category_name]["amount"] += expense.amount

    # Calculate percentages
    if total_expenses:
        for category in stats.values():
            category["percentage"] = category["amount"] / total_expenses * 100

    return stats


def expense_detail(request, expense_id):
    expense = get_object_or_404(Expense, id=expense_id)

    if request.method == "POST":
        form_type = request.POST.get("form_type")

        if form_type == "sub_expense":
            form = SubExpenseForm(request.POST)
            if form.is_valid():
                sub_expense = form.save(commit=False)
                sub_expense.expense = expense
                sub_expense.is_return = "is_return" in request.POST
                # Validate that sub_expense amount doesn't exceed remaining amount
                if sub_expense.amount <= expense.get_remaining_amount():
                    sub_expense.save()
        elif form_type == "edit_sub_expense":
            sub_expense_id = request.POST.get("sub_expense_id")
            if sub_expense_id:
                sub_expense = get_object_or_404(SubExpense, id=sub_expense_id, expense=expense)
                # Calculate the maximum allowed amount for this edit
                max_amount = expense.get_remaining_amount() + sub_expense.amount
                new_amount = Decimal(request.POST.get("amount", 0))

                if new_amount <= max_amount:
                    sub_expense.name = request.POST.get("name")
                    sub_expense.amount = new_amount
                    sub_expense.is_return = "is_return" in request.POST
                    sub_expense.save()
        elif form_type == "delete_sub_expense":
            sub_expense_id = request.POST.get("sub_expense_id")
            if sub_expense_id:
                sub_expense = get_object_or_404(SubExpense, id=sub_expense_id, expense=expense)
                sub_expense.delete()

        return redirect("expense_detail", expense_id=expense_id)
    else:
        form = SubExpenseForm()

    return render(
        request,
        f"{TEMPLATE_VERSION}/expense_detail.html",
        {
            "expense": expense,
            "form": form,
            "sub_expenses": expense.sub_expenses.all(),
        },
    )


@require_POST
def delete_budget(request, year_month):
    try:
        year, month = map(int, year_month.split("-"))
        budget = get_object_or_404(Budget, month__year=year, month__month=month)

        # Create deletion log that expires in 24 hours
        BudgetDeletionLog.objects.create(
            month=budget.month, expires_at=timezone.now() + timedelta(hours=24)
        )

        # Log the deletion before deleting the budget
        BudgetLog.objects.create(
            month=budget.month,
            action="delete",
            details=f"Budget for {budget.month.strftime('%B %Y')} was deleted",
        )
        budget.delete()

        # Clean message without any special characters
        messages.success(request, "Budget has been deleted successfully")

        return JsonResponse({"status": "success"})
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=400)


def get_next_month(request):
    # Get active budgets sorted by month
    active_budgets = Budget.objects.filter(is_archived=False).order_by("month")
    first_budget = active_budgets.first()
    last_budget = active_budgets.last()

    if not first_budget:
        # No active budgets, use earliest archived budget's month or system date
        archived_budget = Budget.objects.filter(is_archived=True).order_by("month").first()
        current_date = (
            archived_budget.month if archived_budget else timezone.now().date().replace(day=1)
        )
    else:
        current_date = last_budget.month + relativedelta(months=1)

    return JsonResponse({"next_month": current_date.strftime("%B %Y")})


def archive_budget(request, year_month):
    # Parse year and month from the year_month parameter
    try:
        year_month_parts = year_month.split("-")
        year = int(year_month_parts[0])
        month = int(year_month_parts[1])
    except (ValueError, IndexError):
        messages.error(request, "Invalid date format. Expected: YYYY-MM")
        return redirect("home")

    # Find budget by year and month
    budget = get_object_or_404(Budget, month__year=year, month__month=month)

    # Check if already archived
    if budget.is_archived:
        messages.info(request, f"Budget for {budget.month.strftime('%B %Y')} is already archived.")
        return redirect("home")

    try:
        # Mark as archived
        budget.is_archived = True
        budget.save(update_fields=["is_archived"])

        # Create archive entry
        ArchivedBudget.objects.create(budget=budget)

        # Create log entry
        BudgetLog.objects.create(
            month=budget.month,
            action="update",
            details=f"Budget archived on {timezone.now().strftime('%Y-%m-%d %H:%M')}",
        )

        messages.success(
            request, f"Budget for {budget.month.strftime('%B %Y')} archived successfully."
        )
    except Exception as e:
        messages.error(request, f"Error archiving budget: {str(e)}")

    return redirect("home")


def view_archives(request):
    archived_budgets = ArchivedBudget.objects.all().select_related("budget")

    # Group archives by year
    archives_by_year = {}
    for archive in archived_budgets:
        year = archive.budget.month.year
        if year not in archives_by_year:
            archives_by_year[year] = []
        archives_by_year[year].append(archive)

    context = {"archives_by_year": archives_by_year}
    return render(request, f"{TEMPLATE_VERSION}/archives.html", context)


@require_POST
def delete_archived_budget(request, year_month):
    try:
        year, month = map(int, year_month.split("-"))
        archived_budget = get_object_or_404(
            ArchivedBudget.objects.select_related("budget"),
            budget__month__year=year,
            budget__month__month=month,
        )

        # Store month info before deletion for message
        month_str = archived_budget.budget.month.strftime("%B %Y")

        # Delete both the archive entry and the budget
        try:
            budget = archived_budget.budget
            archived_budget.delete()  # Delete the archive entry first
            budget.delete()  # Then delete the budget
        except Exception:
            raise

        messages.success(request, f"Archived budget for {month_str} has been deleted")
        return JsonResponse({"status": "success"})
    except Exception as e:
        return JsonResponse(
            {"status": "error", "message": f"Error deleting archived budget: {str(e)}"},
            status=400,
        )


def category_list(request):
    categories = Category.objects.all()
    form = CategoryForm()

    if request.method == "POST":
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Category created successfully!")
            return redirect("category_list")

    return render(
        request,
        f"{TEMPLATE_VERSION}/category_list.html",
        {"categories": categories, "form": form},
    )


def category_edit(request, slug):
    category = get_object_or_404(Category, slug=slug)
    if request.method == "POST":
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, "Category updated successfully!")
            return redirect("category_list")
    else:
        form = CategoryForm(instance=category)

    return render(
        request,
        f"{TEMPLATE_VERSION}/category_edit.html",
        {"form": form, "category": category},
    )


@require_POST
def category_delete(request, slug):
    category = get_object_or_404(Category, slug=slug)
    try:
        category.delete()
        messages.success(request, "Category deleted successfully!")
    except Exception as e:
        messages.error(request, f"Error deleting category: {str(e)}")
    return redirect("category_list")


def handle_income_update(request, budget):
    income = request.POST.get("income")
    currency = request.POST.get("currency")
    reason = request.POST.get("reason")

    if income:
        old_income = budget.income
        old_currency = budget.currency

        budget.income = Decimal(income)
        budget.currency = currency
        budget.save()

        # Log income change
        IncomeHistory.objects.create(
            budget=budget,
            old_amount=old_income,
            new_amount=budget.income,
            old_currency=old_currency,
            new_currency=currency,
            reason=reason,
        )

        messages.success(request, "Income updated successfully!")

    return redirect("budget_detail", year=budget.month.year, month=budget.month.month)


def handle_expense_update(request, budget):
    """Handle updating or creating budget expenses."""
    expense_id = request.POST.get("expense_id")
    name = request.POST.get("name")
    amount = request.POST.get("amount")
    is_recurring = request.POST.get("is_recurring") == "on"
    category_id = request.POST.get("category")

    try:
        if expense_id:
            # Update existing expense
            expense = get_object_or_404(Expense, id=expense_id, budget=budget)

            # Store old values for logging
            old_values = {
                "name": expense.name,
                "amount": expense.amount,
                "category_id": expense.category_id,
                "is_recurring": expense.is_recurring,
            }

            # Update fields
            expense.name = name
            expense.amount = Decimal(amount)
            expense.is_recurring = is_recurring
            expense.category_id = category_id if category_id else None
            expense.save()

            # Log the update
            changes = []
            if old_values["name"] != name:
                changes.append(f"name from '{old_values['name']}' to '{name}'")
            if old_values["amount"] != Decimal(amount):
                changes.append(
                    f"amount from {budget.currency} {old_values['amount']} to "
                    f"{budget.currency} {amount}"
                )
            if old_values["category_id"] != category_id:
                changes.append("category")

            if changes:
                RecentUpdate.objects.create(
                    budget=budget,
                    action_type="expense_updated",
                    description=f"Updated expense: {expense.name} ("
                    f"changed {', '.join(changes)})",
                    amount=expense.amount,
                    category=expense.category,
                )

            messages.success(request, "Expense updated successfully!")
        else:
            # Create new expense
            expense = Expense.objects.create(
                budget=budget,
                name=name,
                amount=Decimal(amount),
                is_recurring=is_recurring,
                category_id=category_id if category_id else None,
            )
            messages.success(request, "Expense added successfully!")

    except Exception as e:
        messages.error(request, f"Error handling expense: {str(e)}")

    return redirect("budget_detail", year=budget.month.year, month=budget.month.month)


def handle_expense_delete(request, budget):
    expense_id = request.POST.get("expense_id")
    if expense_id:
        try:
            expense = get_object_or_404(Expense, id=expense_id, budget=budget)
            expense_name = expense.name
            expense.delete()
            messages.success(request, f'Expense "{expense_name}" deleted successfully!')
        except Exception as e:
            messages.error(request, f"Error deleting expense: {str(e)}")

    return redirect("budget_detail", year=budget.month.year, month=budget.month.month)


# Goal Views
@login_required
def goal_list(request):
    """
    Display a list of user's financial goals
    """
    goals = Goal.objects.filter(user=request.user)
    active_goals = goals.filter(is_active=True)
    completed_goals = goals.filter(current_amount__gte=F("target_amount"))
    inactive_goals = goals.filter(is_active=False).exclude(id__in=completed_goals)

    context = {
        "active_goals": active_goals,
        "completed_goals": completed_goals,
        "inactive_goals": inactive_goals,
    }

    return render(request, f"{TEMPLATE_VERSION}/goals/goal_list.html", context)


@login_required
def goal_detail(request, goal_id):
    """
    Display details of a specific goal including contribution history
    """
    goal = get_object_or_404(Goal, id=goal_id, user=request.user)
    contributions = goal.contributions.all().order_by("-date")

    # Paginate contributions
    paginator = Paginator(contributions, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # Form for adding contributions
    if request.method == "POST":
        form = GoalContributionForm(request.POST)
        if form.is_valid():
            contribution = form.save(commit=False)
            contribution.goal = goal
            contribution.save()

            # Update goal's current amount
            goal.current_amount += contribution.amount
            goal.save(update_fields=["current_amount"])

            messages.success(request, f"Added contribution of {contribution.amount}")
            return redirect("goal_detail", goal_id=goal.id)
    else:
        form = GoalContributionForm()

    context = {
        "goal": goal,
        "contributions_page": page_obj,
        "form": form,
        "monthly_needed": goal.monthly_contribution_needed(),
        "on_track": goal.is_on_track(),
        "progress": goal.progress_percentage,
    }

    return render(request, f"{TEMPLATE_VERSION}/goals/goal_detail.html", context)


@login_required
def goal_create(request):
    """
    Create a new financial goal
    """
    if request.method == "POST":
        form = GoalForm(request.POST, user=request.user)
        if form.is_valid():
            goal = form.save(commit=False)
            goal.user = request.user
            goal.save()

            messages.success(request, f"Created new goal: {goal.name}")
            return redirect("goal_detail", goal_id=goal.id)
    else:
        form = GoalForm(user=request.user)

    context = {
        "form": form,
        "title": "Create New Goal",
    }

    return render(request, f"{TEMPLATE_VERSION}/goals/goal_form.html", context)


@login_required
def goal_edit(request, goal_id):
    """
    Edit an existing financial goal
    """
    goal = get_object_or_404(Goal, id=goal_id, user=request.user)

    if request.method == "POST":
        form = GoalForm(request.POST, instance=goal, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, f"Updated goal: {goal.name}")
            return redirect("goal_detail", goal_id=goal.id)
    else:
        form = GoalForm(instance=goal, user=request.user)

    context = {
        "form": form,
        "goal": goal,
        "title": "Edit Goal",
    }

    return render(request, f"{TEMPLATE_VERSION}/goals/goal_form.html", context)


@login_required
@require_POST
def goal_delete(request, goal_id):
    """
    Delete a financial goal
    """
    goal = get_object_or_404(Goal, id=goal_id, user=request.user)
    name = goal.name
    goal.delete()

    messages.success(request, f"Deleted goal: {name}")
    return redirect("goal_list")


@login_required
@require_POST
def add_contribution(request, goal_id):
    """
    Add a contribution to a goal from the goal detail page
    """
    goal = get_object_or_404(Goal, id=goal_id, user=request.user)

    form = GoalContributionForm(request.POST)
    if form.is_valid():
        contribution = form.save(commit=False)
        contribution.goal = goal
        contribution.save()

        # Update goal's current amount
        goal.current_amount += contribution.amount
        goal.save(update_fields=["current_amount"])

        messages.success(request, f"Added contribution of {contribution.amount}")
    else:
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(request, f"Error in {field}: {error}")

    return redirect("goal_detail", goal_id=goal.id)
