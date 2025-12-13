import calendar
from datetime import date, datetime
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.humanize.templatetags.humanize import intcomma
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.views import View
from django.views.generic import TemplateView


class LoginRequiredView(LoginRequiredMixin, View):
    """Base view that requires login for all Views."""

    pass


class LoginRequiredTemplateView(LoginRequiredMixin, TemplateView):
    """Base view that requires login for all TemplateViews."""

    pass

from budgetapp.models import (
    Budget,
    Category,
    Debt,
    DebtTransaction,
    Expense,
    IncomeHistory,
    SubExpense,
    Tag,
)


class UnicodeJsonResponse(JsonResponse):
    """Custom JsonResponse that doesn't escape Unicode characters."""

    def __init__(self, data, **kwargs):
        kwargs.setdefault("json_dumps_params", {"ensure_ascii": False})
        super().__init__(data, **kwargs)


class OfflineView(TemplateView):
    """Offline fallback page for PWA."""

    template_name = "minimal/offline.html"


class HomeView(LoginRequiredTemplateView):
    template_name = "minimal/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        months = [calendar.month_name[i] for i in range(1, 13)]
        abbrs = [calendar.month_abbr[i] for i in range(1, 13)]
        today = date.today()
        budgets_by_month = {
            b.month.month: b
            for b in Budget.objects.filter(user=self.request.user, is_archived=False)
        }
        months_data = []
        for i, (month_name, abbr) in enumerate(zip(months, abbrs), 1):
            if i < today.month:
                status = "past" if i in budgets_by_month else "future"
            elif i == today.month:
                status = "current" if i in budgets_by_month else "future"
            else:
                status = "future-created" if i in budgets_by_month else "future"
            months_data.append(
                {
                    "name": month_name,
                    "abbr": abbr,
                    "status": status,
                    "number": i,
                }
            )
        # Group into 3 rows of 4 months each, right-to-left
        months_grid = []
        for i in range(0, 12, 4):
            row = months_data[i : i + 4][::-1]  # reverse for right-to-left
            months_grid.append(row)
        context["months_grid"] = months_grid
        context["year"] = today.year
        return context


class BudgetDetailView(LoginRequiredTemplateView):
    template_name = "minimal/budget_detail_pages/budget_detail.html"

    def _format_currency(self, val: float) -> str:
        """
        Format a float value as a string with comma as thousands separator and two decimal places.
        Example: 12345.67 -> '12,345.67'
        """
        return intcomma(f"{val:,.2f}")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        year = self.kwargs.get("year")
        month = self.kwargs.get("month")
        budget_date = timezone.datetime(year=year, month=month, day=1).date()
        budget = get_object_or_404(Budget, month=budget_date, user=self.request.user)

        # Get all expenses for this budget
        expenses_qs = budget.expenses.all().order_by("created_at")
        total_expenses = sum(e.amount for e in expenses_qs)
        categories = Category.objects.filter(user=self.request.user)
        tags = Tag.objects.filter(user=self.request.user).order_by("name")

        # Format numbers for display
        budget_income_display = self._format_currency(budget.income)
        total_expenses_display = self._format_currency(total_expenses)
        remaining_budget_display = self._format_currency(budget.get_remaining_budget())

        # Prepare expenses with amount_display and sub_expenses with amount_display
        expenses = []
        for expense in expenses_qs:
            sub_expenses = [
                {
                    "id": sub.id,
                    "name": sub.name,
                    "amount": sub.amount,
                    "amount_display": self._format_currency(sub.amount),
                    "is_return": sub.is_return,
                }
                for sub in expense.sub_expenses.all()
            ]
            subexpense_total = expense.subexpense_total
            total_returns = expense.get_total_returns()
            remaining_amount = expense.get_remaining_amount()
            expenses.append(
                {
                    "id": expense.id,
                    "name": expense.name,
                    "amount": expense.amount,
                    "amount_display": self._format_currency(expense.amount),
                    "category": expense.category,
                    "tag_foreign_key": expense.tag_foreign_key,
                    "get_tag_display": (
                        expense.tag_foreign_key.name if expense.tag_foreign_key else "None"
                    ),
                    "is_recurring": expense.is_recurring,
                    "sub_expenses": sub_expenses,
                    "sub_expenses_exists": expense.sub_expenses.exists(),
                    "subexpense_total": subexpense_total,
                    "subexpense_total_display": self._format_currency(subexpense_total),
                    "returns": total_returns,
                    "total_returns": self._format_currency(float(total_returns)),
                    "remaining_amount": self._format_currency(float(remaining_amount)),
                }
            )

        # Prepare category stats for display
        expenses_by_category = {}
        if expenses_qs.exists():
            category_totals = {}
            for expense in expenses_qs:
                cat = expense.category.name if expense.category else "Uncategorized"
                if cat not in category_totals:
                    category_totals[cat] = {
                        "amount": 0,
                        "color": expense.category.color if expense.category else "#e0e0e0",
                    }
                category_totals[cat]["amount"] += float(expense.amount)
            for cat, data in category_totals.items():
                percent = (data["amount"] / float(total_expenses) * 100) if total_expenses else 0
                expenses_by_category[cat] = {
                    "amount": data["amount"],
                    "amount_display": self._format_currency(data["amount"]),
                    "color": data["color"],
                    "percentage": percent,
                    "percentage_display": f"{percent:.1f}",
                }

        # Calculate tag totals for display using tag_foreign_key
        tag_totals = {}
        tag_labels = {}
        for expense in expenses_qs:
            if expense.tag_foreign_key:
                tag_name = expense.tag_foreign_key.name
                if tag_name not in tag_totals:
                    tag_totals[tag_name] = 0
                    tag_labels[tag_name] = tag_name
                tag_totals[tag_name] += float(expense.amount)

        context.update(
            {
                "budget": budget,
                "expenses": expenses,
                "categories": categories,
                "tags": tags,
                "total_expenses": total_expenses,
                "currency_choices": Budget.get_currency_choices(),
                "budget_income_display": budget_income_display,
                "total_expenses_display": total_expenses_display,
                "remaining_budget_display": remaining_budget_display,
                "expenses_by_category": expenses_by_category,
                "tag_totals": tag_totals,
                "tag_labels": tag_labels,
            }
        )
        return context


class CategoryStatsView(LoginRequiredView):
    """View for AJAX updates to category statistics."""

    def _format_currency(self, val: float) -> str:
        """Format a float value as a string with comma
        as thousands separator and two decimal places."""
        return intcomma(f"{val:,.2f}")

    def get(self, request, *args, **kwargs):
        year = kwargs.get("year")
        month = kwargs.get("month")
        budget_date = timezone.datetime(year=year, month=month, day=1).date()
        budget = get_object_or_404(Budget, month=budget_date)

        # Get all expenses for this budget
        expenses_qs = budget.expenses.all()
        total_expenses = sum(e.amount for e in expenses_qs)

        # Prepare category stats for display
        expenses_by_category = {}
        if expenses_qs.exists():
            category_totals = {}
            for expense in expenses_qs:
                cat = expense.category.name if expense.category else "Uncategorized"
                if cat not in category_totals:
                    category_totals[cat] = {
                        "amount": 0,
                        "color": expense.category.color if expense.category else "#e0e0e0",
                    }
                category_totals[cat]["amount"] += float(expense.amount)
            for cat, data in category_totals.items():
                percent = (data["amount"] / float(total_expenses) * 100) if total_expenses else 0
                expenses_by_category[cat] = {
                    "amount": data["amount"],
                    "amount_display": self._format_currency(data["amount"]),
                    "color": data["color"],
                    "percentage": percent,
                    "percentage_display": f"{percent:.1f}",
                }

        context = {
            "budget": budget,
            "expenses_by_category": expenses_by_category,
        }

        # Render the category stats template
        html = render_to_string("minimal/budget_detail_pages/category_stats_content.html", context)
        return JsonResponse({"html": html})


class TagStatsView(LoginRequiredView):
    """View for AJAX updates to tag statistics."""

    def _format_currency(self, val: float) -> str:
        """Format a float value as a string with comma
        as thousands separator and two decimal places."""
        return intcomma(f"{val:,.2f}")

    def get(self, request, *args, **kwargs):
        year = kwargs.get("year")
        month = kwargs.get("month")
        budget_date = timezone.datetime(year=year, month=month, day=1).date()
        budget = get_object_or_404(Budget, month=budget_date)

        # Get all expenses for this budget
        expenses_qs = budget.expenses.all()

        # Calculate tag totals for display using tag_foreign_key
        tag_totals = {}
        tag_labels = {}
        for expense in expenses_qs:
            if expense.tag_foreign_key:
                tag_name = expense.tag_foreign_key.name
                if tag_name not in tag_totals:
                    tag_totals[tag_name] = 0
                    tag_labels[tag_name] = tag_name
                tag_totals[tag_name] += float(expense.amount)

        context = {
            "budget": budget,
            "tag_totals": tag_totals,
            "tag_labels": tag_labels,
        }

        # Render the tag stats template
        html = render_to_string("minimal/budget_detail_pages/tag_stats_content.html", context)
        return JsonResponse({"html": html})


class SummaryCardsView(LoginRequiredView):
    """View for getting summary cards."""

    def _format_currency(self, val: float) -> str:
        return intcomma(f"{val:,.2f}")

    def get(self, request, *args, **kwargs):
        year = kwargs.get("year")
        month = kwargs.get("month")
        budget_date = timezone.datetime(year=year, month=month, day=1).date()
        budget = get_object_or_404(Budget, month=budget_date)

        # Get all expenses for this budget
        expenses_qs = budget.expenses.all()
        total_expenses = sum(e.amount for e in expenses_qs)

        # Format numbers for display
        budget_income_display = self._format_currency(budget.income)
        total_expenses_display = self._format_currency(total_expenses)
        remaining_budget_display = self._format_currency(budget.get_remaining_budget())

        # Render the summary cards section
        html = render_to_string(
            "minimal/budget_detail_pages/summary_cards.html",
            {
                "budget": budget,
                "budget_income_display": budget_income_display,
                "total_expenses_display": total_expenses_display,
                "remaining_budget_display": remaining_budget_display,
            },
        )

        return JsonResponse({"html": html})


class BudgetCreateView(LoginRequiredView):
    """Class-based view for creating a new budget."""

    def get(self, request, *args, **kwargs):
        """Show modal to choose between blank budget or copy from previous."""
        return JsonResponse(
            {
                "status": "success",
                "showModal": True,
                "title": "Create New Budget",
                "message": "Would you like to create a blank \
                budget or copy recurring expenses from the previous budget?",
            }
        )

    def post(self, request, *args, **kwargs):
        copy_recurring_param = request.POST.get("copy_recurring", "true")
        copy_recurring = copy_recurring_param.lower() == "true"

        target_year = request.POST.get("target_year")
        target_month = request.POST.get("target_month")

        # Determine the target month for budget creation
        if target_year and target_month:
            # Use the specified year and month
            target_month_date = timezone.datetime(
                year=int(target_year), month=int(target_month), day=1
            ).date()
        else:
            # Fallback to the original logic (next month after last budget)
            last_budget = Budget.objects.filter(user=request.user).order_by("-month").first()
            if last_budget:
                target_month_date = (
                    last_budget.month.replace(day=1) + timezone.timedelta(days=32)
                ).replace(day=1)
            else:
                target_month_date = timezone.now().date().replace(day=1)

        # Check if budget already exists for this month
        if Budget.objects.filter(user=request.user, month=target_month_date).exists():
            return JsonResponse(
                {
                    "status": "error",
                    "message": f"Budget for {target_month_date.strftime('%B %Y')} already exists.",
                },
                status=400,
            )

        # Create new budget
        budget = Budget.objects.create(user=request.user, month=target_month_date)

        # Copy recurring expenses and income from previous budget if requested
        if copy_recurring:
            # Get the budget before the one we just created
            previous_budget = (
                Budget.objects.filter(user=request.user, month__lt=target_month_date)
                .order_by("-month")
                .first()
            )
            if previous_budget:
                # Copy income from previous budget
                budget.income = previous_budget.income
                budget.save()

                # Copy recurring expenses
                recurring_expenses = previous_budget.expenses.filter(is_recurring=True)
                for expense in recurring_expenses:
                    Expense.objects.create(
                        budget=budget,
                        name=expense.name,
                        amount=expense.amount,
                        is_recurring=True,
                        category=expense.category,
                        tag_foreign_key=expense.tag_foreign_key,
                    )
                # Add success message about copied expenses and income
                if recurring_expenses.exists():
                    messages.success(
                        request,
                        f"Copied income and \n"
                        f"{recurring_expenses.count()} recurring expense(s) from previous budget",
                    )
                else:
                    messages.success(request, "Copied income from previous budget")
            else:
                messages.error(request, "No previous budget found to copy from")

        messages.success(
            request, f'Budget for {target_month_date.strftime("%B %Y")} has been created'
        )

        # Return JSON response with redirect URL
        redirect_url = reverse(
            "minimal:budget_detail",
            kwargs={"year": target_month_date.year, "month": target_month_date.month},
        )
        return JsonResponse(
            {
                "status": "success",
                "message": f'Budget for {target_month_date.strftime("%B %Y")} has been created',
                "redirect": redirect_url,
            }
        )


class BudgetDeleteView(LoginRequiredView):
    """Class-based view for deleting a budget."""

    def post(self, request, *args, **kwargs):
        year = kwargs.get("year")
        month = kwargs.get("month")
        budget_date = timezone.datetime(year=year, month=month, day=1).date()

        try:
            budget = Budget.objects.get(user=request.user, month=budget_date)
        except Budget.DoesNotExist:
            return JsonResponse(
                {
                    "status": "error",
                    "message": f"Budget for {budget_date.strftime('%B %Y')} does not exist.",
                },
                status=404,
            )

        # Store budget info for the message
        budget_month_str = budget.month.strftime("%B %Y")

        # Delete the budget (this will cascade delete all related data)
        budget.delete()

        messages.success(request, f"Budget for {budget_month_str} has been deleted")

        return JsonResponse(
            {
                "status": "success",
                "message": f"Budget for {budget_month_str} has been successfully deleted.",
            }
        )


class IncomeUpdateView(LoginRequiredView):
    """Class-based view for updating budget income."""

    def post(self, request, *args, **kwargs):
        year = kwargs.get("year")
        month = kwargs.get("month")
        budget_date = timezone.datetime(year=year, month=month, day=1).date()
        budget = get_object_or_404(Budget, month=budget_date)

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

            # Format for display
            income_display = intcomma(f"{float(budget.income):,.2f}")
            remaining_budget = budget.get_remaining_budget()
            remaining_budget_display = intcomma(f"{float(remaining_budget):,.2f}")

            return JsonResponse(
                {
                    "status": "success",
                    "message": "Income updated successfully!",
                    "income": float(budget.income),
                    "income_display": income_display,
                    "currency": currency,
                    "remaining_budget": float(remaining_budget),
                    "remaining_budget_display": remaining_budget_display,
                }
            )

        return JsonResponse({"status": "error", "message": "Income value is required"}, status=400)


class ExpenseCreateUpdateView(LoginRequiredView):
    """Class-based view for creating or updating expenses."""

    def _format_currency(self, val: float) -> str:
        """Format a float value as a string with comma
        as thousands separator and two decimal places."""
        return intcomma(f"{val:,.2f}")

    def post(self, request, *args, **kwargs):
        year = kwargs.get("year")
        month = kwargs.get("month")
        budget_date = timezone.datetime(year=year, month=month, day=1).date()
        budget = get_object_or_404(Budget, month=budget_date)

        expense_id = request.POST.get("expense_id")
        name = request.POST.get("name")
        amount = request.POST.get("amount")
        is_recurring = request.POST.get("is_recurring") == "on"
        category_id = request.POST.get("category")
        tag_id = request.POST.get("tag")

        try:
            if expense_id:
                # Update existing expense
                expense = get_object_or_404(Expense, id=expense_id, budget=budget)
                expense.name = name
                expense.amount = Decimal(amount)
                expense.is_recurring = is_recurring
                expense.category_id = category_id if category_id else None
                expense.tag_foreign_key_id = tag_id if tag_id else None
                expense.save()

                # Get category name for response
                category_name = expense.category.name if expense.category else "Uncategorized"
                category_color = expense.category.color if expense.category else "#e0e0e0"

                return UnicodeJsonResponse(
                    {
                        "status": "success",
                        "message": "Expense updated successfully!",
                        "expense": {
                            "id": expense.id,
                            "name": expense.name,
                            "amount": float(expense.amount),
                            "amount_display": self._format_currency(expense.amount),
                            "is_recurring": expense.is_recurring,
                            "category_id": expense.category_id,
                            "category_name": category_name,
                            "category_color": category_color,
                            "tag_foreign_key_id": expense.tag_foreign_key_id,
                            "tag_foreign_key": {
                                "id": (
                                    expense.tag_foreign_key.id if expense.tag_foreign_key else None
                                ),
                                "name": (
                                    expense.tag_foreign_key.name
                                    if expense.tag_foreign_key
                                    else None
                                ),
                                "color": (
                                    expense.tag_foreign_key.color
                                    if expense.tag_foreign_key
                                    else None
                                ),
                            },
                        },
                        "action": "update",
                    }
                )
            else:
                # Create new expense
                expense = Expense.objects.create(
                    budget=budget,
                    name=name,
                    amount=Decimal(amount),
                    is_recurring=is_recurring,
                    category_id=category_id if category_id else None,
                    tag_foreign_key_id=tag_id if tag_id else None,
                )

                # Get category name for response
                category_name = expense.category.name if expense.category else "Uncategorized"
                category_color = expense.category.color if expense.category else "#e0e0e0"

                # Format sub-expenses for response
                sub_expenses = []

                return UnicodeJsonResponse(
                    {
                        "status": "success",
                        "message": "Expense added successfully!",
                        "expense": {
                            "id": expense.id,
                            "name": expense.name,
                            "amount": float(expense.amount),
                            "amount_display": self._format_currency(expense.amount),
                            "is_recurring": expense.is_recurring,
                            "category_id": expense.category_id,
                            "category_name": category_name,
                            "category_color": category_color,
                            "tag_foreign_key_id": expense.tag_foreign_key_id,
                            "tag_foreign_key": {
                                "id": (
                                    expense.tag_foreign_key.id if expense.tag_foreign_key else None
                                ),
                                "name": (
                                    expense.tag_foreign_key.name
                                    if expense.tag_foreign_key
                                    else None
                                ),
                                "color": (
                                    expense.tag_foreign_key.color
                                    if expense.tag_foreign_key
                                    else None
                                ),
                            },
                            "sub_expenses": sub_expenses,
                            "sub_expenses_exists": False,
                        },
                        "action": "create",
                    }
                )
        except Exception as e:
            return UnicodeJsonResponse(
                {"status": "error", "message": f"Error handling expense: {str(e)}"}, status=400
            )


class ExpenseDeleteView(LoginRequiredView):
    """Class-based view for deleting expenses."""

    def post(self, request, *args, **kwargs):
        year = kwargs.get("year")
        month = kwargs.get("month")
        budget_date = timezone.datetime(year=year, month=month, day=1).date()
        budget = get_object_or_404(Budget, month=budget_date)

        expense_id = request.POST.get("expense_id")
        if expense_id:
            try:
                expense = get_object_or_404(Expense, id=expense_id, budget=budget)
                expense_name = expense.name
                expense_amount = float(expense.amount)
                expense.delete()

                # Calculate new budget totals
                total_expenses = sum(e.amount for e in budget.expenses.all())
                remaining_budget = budget.get_remaining_budget()

                return JsonResponse(
                    {
                        "status": "success",
                        "message": f'Expense "{expense_name}" deleted successfully!',
                        "expense_id": expense_id,
                        "deleted_amount": expense_amount,
                        "new_total_expenses": float(total_expenses),
                        "new_total_expenses_display": intcomma(f"{float(total_expenses):,.2f}"),
                        "new_remaining_budget": float(remaining_budget),
                        "new_remaining_budget_display": intcomma(f"{float(remaining_budget):,.2f}"),
                    }
                )
            except Exception as e:
                return JsonResponse(
                    {"status": "error", "message": f"Error deleting expense: {str(e)}"}, status=400
                )

        return JsonResponse({"status": "error", "message": "No expense ID provided"}, status=400)


class SubExpenseCreateView(LoginRequiredView):
    """Class-based view for creating a new sub-expense."""

    def _format_currency(self, val: float) -> str:
        return intcomma(f"{val:,.2f}")

    def post(self, request, *args, **kwargs):
        expense_id = request.POST.get("expense_id")
        name = request.POST.get("name")
        amount = Decimal(request.POST.get("amount"))
        is_return = request.POST.get("is_return") == "on"
        try:
            expense = get_object_or_404(Expense, id=expense_id)
            sub = SubExpense.objects.create(
                expense=expense,
                name=name,
                amount=amount,
                is_return=is_return,
            )
            # Calculate summary
            total_returns = expense.get_total_returns()
            remaining_amount = expense.get_remaining_amount()
            return JsonResponse(
                {
                    "status": "success",
                    "message": "Sub-expense added successfully!",
                    "subexpense": {
                        "id": sub.id,
                        "name": sub.name,
                        "amount": float(sub.amount),
                        "amount_display": self._format_currency(float(sub.amount)),
                        "is_return": sub.is_return,
                    },
                    "action": "create",
                    "summary": {
                        "total_returns": self._format_currency(float(total_returns)),
                        "remaining_amount": self._format_currency(float(remaining_amount)),
                    },
                }
            )
        except Exception as e:
            return JsonResponse(
                {"status": "error", "message": f"Error adding sub-expense: {str(e)}"}, status=400
            )


class SubExpenseUpdateView(LoginRequiredView):
    """Class-based view for updating a sub-expense."""

    def _format_currency(self, val: float) -> str:
        return intcomma(f"{val:,.2f}")

    def post(self, request, *args, **kwargs):
        subexpense_id = request.POST.get("subexpense_id")
        name = request.POST.get("name")
        amount = Decimal(request.POST.get("amount"))
        is_return = request.POST.get("is_return") == "on"
        try:
            sub = get_object_or_404(SubExpense, id=subexpense_id)
            sub.name = name
            sub.amount = amount
            sub.is_return = is_return
            sub.save()
            expense = sub.expense
            # Calculate summary
            total_returns = expense.get_total_returns()
            remaining_amount = expense.get_remaining_amount()
            return JsonResponse(
                {
                    "status": "success",
                    "message": "Sub-expense updated successfully!",
                    "subexpense": {
                        "id": sub.id,
                        "name": sub.name,
                        "amount": float(sub.amount),
                        "amount_display": self._format_currency(float(sub.amount)),
                        "is_return": sub.is_return,
                    },
                    "action": "update",
                    "summary": {
                        "total_returns": self._format_currency(float(total_returns)),
                        "remaining_amount": self._format_currency(float(remaining_amount)),
                    },
                }
            )
        except Exception as e:
            return JsonResponse(
                {"status": "error", "message": f"Error updating sub-expense: {str(e)}"}, status=400
            )


class SubExpenseDeleteView(LoginRequiredView):
    """Class-based view for deleting a sub-expense."""

    def post(self, request, *args, **kwargs):
        subexpense_id = request.POST.get("subexpense_id")
        try:
            sub = get_object_or_404(SubExpense, id=subexpense_id)
            expense = sub.expense
            sub.delete()
            # Calculate summary
            total_returns = expense.get_total_returns()
            remaining_amount = expense.get_remaining_amount()
            return JsonResponse(
                {
                    "status": "success",
                    "message": "Sub-expense deleted successfully!",
                    "subexpense_id": subexpense_id,
                    "action": "delete",
                    "summary": {
                        "total_returns": intcomma(f"{float(total_returns):,.2f}"),
                        "remaining_amount": intcomma(f"{float(remaining_amount):,.2f}"),
                    },
                }
            )
        except Exception as e:
            return JsonResponse(
                {"status": "error", "message": f"Error deleting sub-expense: {str(e)}"}, status=400
            )


class TagManagementView(LoginRequiredTemplateView):
    """View for managing tags."""

    template_name = "minimal/tag_management.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["tags"] = Tag.objects.filter(user=self.request.user).order_by("name")
        return context


class TagCreateView(LoginRequiredView):
    """View for creating new tags via AJAX."""

    def post(self, request, *args, **kwargs):
        name = request.POST.get("name")
        description = request.POST.get("description", "")
        color = request.POST.get("color", "#2196f3")

        if not name:
            return JsonResponse({"status": "error", "message": "Tag name is required"}, status=400)

        try:
            tag = Tag.objects.create(
                user=request.user, name=name, description=description, color=color
            )
            return JsonResponse(
                {
                    "status": "success",
                    "message": f'Tag "{name}" created successfully!',
                    "tag": {
                        "id": tag.id,
                        "name": tag.name,
                        "description": tag.description,
                        "color": tag.color,
                        "created_at": tag.created_at.strftime("%Y-%m-%d %H:%M"),
                    },
                }
            )
        except Exception as e:
            return JsonResponse(
                {"status": "error", "message": f"Error creating tag: {str(e)}"}, status=400
            )


class TagUpdateView(LoginRequiredView):
    """View for updating tags via AJAX."""

    def post(self, request, *args, **kwargs):
        tag_id = request.POST.get("tag_id")
        name = request.POST.get("name")
        description = request.POST.get("description", "")
        color = request.POST.get("color", "#2196f3")

        if not tag_id or not name:
            return JsonResponse(
                {"status": "error", "message": "Tag ID and name are required"}, status=400
            )

        try:
            tag = get_object_or_404(Tag, id=tag_id, user=request.user)
            tag.name = name
            tag.description = description
            tag.color = color
            tag.save()

            return JsonResponse(
                {
                    "status": "success",
                    "message": f'Tag "{name}" updated successfully!',
                    "tag": {
                        "id": tag.id,
                        "name": tag.name,
                        "description": tag.description,
                        "color": tag.color,
                        "updated_at": tag.updated_at.strftime("%Y-%m-%d %H:%M"),
                    },
                }
            )
        except Exception as e:
            return JsonResponse(
                {"status": "error", "message": f"Error updating tag: {str(e)}"}, status=400
            )


class TagDeleteView(LoginRequiredView):
    """View for deleting tags via AJAX."""

    def post(self, request, *args, **kwargs):
        tag_id = request.POST.get("tag_id")

        if not tag_id:
            return JsonResponse({"status": "error", "message": "Tag ID is required"}, status=400)

        try:
            tag = get_object_or_404(Tag, id=tag_id, user=request.user)
            tag_name = tag.name
            tag.delete()

            return JsonResponse(
                {
                    "status": "success",
                    "message": f'Tag "{tag_name}" deleted successfully!',
                    "tag_id": tag_id,
                }
            )
        except Exception as e:
            return JsonResponse(
                {"status": "error", "message": f"Error deleting tag: {str(e)}"}, status=400
            )


class CategoryManagementView(LoginRequiredTemplateView):
    """View for managing categories."""

    template_name = "minimal/category_management.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = Category.objects.filter(user=self.request.user).order_by("name")
        return context


class CategoryListView(LoginRequiredView):
    """View for listing categories via AJAX."""

    def get(self, request, *args, **kwargs):
        category_id = request.GET.get("category_id")

        if category_id:
            # Return specific category for editing
            try:
                category = Category.objects.get(id=category_id, user=request.user)
                return JsonResponse(
                    {
                        "success": True,
                        "category": {
                            "id": category.id,
                            "name": category.name,
                            "description": category.description,
                            "color": category.color,
                        },
                    }
                )
            except Category.DoesNotExist:
                return JsonResponse({"success": False, "error": "Category not found"}, status=404)
        else:
            # Return all categories for this user
            categories = Category.objects.filter(user=request.user).order_by("name")
            return JsonResponse(
                {
                    "success": True,
                    "categories": [
                        {
                            "id": category.id,
                            "name": category.name,
                            "description": category.description,
                            "color": category.color,
                        }
                        for category in categories
                    ],
                }
            )


class CategoryCreateView(LoginRequiredView):
    """View for creating new categories via AJAX."""

    def post(self, request, *args, **kwargs):
        name = request.POST.get("name")
        description = request.POST.get("description", "")
        color = request.POST.get("color", "#2196f3")

        if not name:
            return JsonResponse(
                {"success": False, "error": "Category name is required"}, status=400
            )

        try:
            category = Category.objects.create(
                user=request.user, name=name, description=description, color=color
            )
            return JsonResponse(
                {
                    "success": True,
                    "message": f'Category "{name}" created successfully!',
                    "category": {
                        "id": category.id,
                        "name": category.name,
                        "description": category.description,
                        "color": category.color,
                    },
                }
            )
        except Exception as e:
            return JsonResponse(
                {"success": False, "error": f"Error creating category: {str(e)}"}, status=400
            )


class CategoryUpdateView(LoginRequiredView):
    """View for updating categories via AJAX."""

    def post(self, request, *args, **kwargs):
        category_id = request.POST.get("category_id")
        name = request.POST.get("name")
        description = request.POST.get("description", "")
        color = request.POST.get("color", "#2196f3")

        if not category_id or not name:
            return JsonResponse(
                {"success": False, "error": "Category ID and name are required"}, status=400
            )

        try:
            category = get_object_or_404(Category, id=category_id, user=request.user)
            category.name = name
            category.description = description
            category.color = color
            category.save()

            return JsonResponse(
                {
                    "success": True,
                    "message": f'Category "{name}" updated successfully!',
                    "category": {
                        "id": category.id,
                        "name": category.name,
                        "description": category.description,
                        "color": category.color,
                    },
                }
            )
        except Exception as e:
            return JsonResponse(
                {"success": False, "error": f"Error updating category: {str(e)}"}, status=400
            )


class CategoryDeleteView(LoginRequiredView):
    """View for deleting categories via AJAX."""

    def post(self, request, *args, **kwargs):
        category_id = request.POST.get("category_id")

        if not category_id:
            return JsonResponse({"success": False, "error": "Category ID is required"}, status=400)

        try:
            category = get_object_or_404(Category, id=category_id, user=request.user)
            category_name = category.name

            # Check if category is being used by any expenses
            if category.expenses.exists():
                error_message = (
                    f'Cannot delete category "{category_name}" because it is being used by '
                    f"existing expenses."
                )
                return JsonResponse(
                    {
                        "success": False,
                        "error": error_message,
                    },
                    status=400,
                )

            category.delete()

            return JsonResponse(
                {
                    "success": True,
                    "message": f'Category "{category_name}" deleted successfully!',
                    "category_id": category_id,
                }
            )
        except Exception as e:
            return JsonResponse(
                {"success": False, "error": f"Error deleting category: {str(e)}"}, status=400
            )


# Debt Views
class DebtListView(LoginRequiredTemplateView):
    """View for listing all debts."""

    template_name = "minimal/debts/debt_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        active_debts = Debt.objects.filter(
            user=self.request.user, is_active=True
        ).order_by("-created_at")
        completed_debts = Debt.objects.filter(
            user=self.request.user, is_active=False
        ).order_by("-created_at")

        # Check and update debt status (disable tags if fully repaid)
        for debt in active_debts:
            debt.check_and_update_status()

        context.update(
            {
                "active_debts": active_debts,
                "completed_debts": completed_debts,
            }
        )
        return context


class DebtDetailView(LoginRequiredTemplateView):
    """View for displaying debt details."""

    template_name = "minimal/debts/debt_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        debt_id = self.kwargs.get("debt_id")
        debt = get_object_or_404(Debt, id=debt_id, user=self.request.user)
        transactions = debt.transactions.all().order_by("-date")

        # Check and update debt status
        debt.check_and_update_status()

        # Calculate additional statistics
        total_borrowed = sum(t.amount for t in transactions)

        context.update(
            {
                "debt": debt,
                "transactions_page": transactions,  # Match template variable name
                "total_borrowed": total_borrowed,
            }
        )
        return context


class DebtCreateView(LoginRequiredView):
    """View for creating new debts via AJAX."""

    def post(self, request, *args, **kwargs):
        name = request.POST.get("name")
        description = request.POST.get("description", "")
        total_amount = request.POST.get("total_amount")

        if not name or not total_amount:
            return JsonResponse(
                {"success": False, "error": "Name and total amount are required"}, status=400
            )

        try:
            total_amount = Decimal(total_amount)
            if total_amount <= 0:
                return JsonResponse(
                    {"success": False, "error": "Total amount must be greater than zero"},
                    status=400,
                )

            debt = Debt.objects.create(
                user=request.user, name=name, description=description, total_amount=total_amount
            )

            return JsonResponse(
                {
                    "success": True,
                    "message": f'Debt "{name}" created successfully!',
                    "debt": {
                        "id": debt.id,
                        "name": debt.name,
                        "description": debt.description,
                        "total_amount": str(debt.total_amount),
                        "borrowed_amount": str(debt.borrowed_amount),
                        "repaid_amount": str(debt.repaid_amount),
                        "remaining_to_repay": str(debt.remaining_to_repay),
                        "repayment_progress_percentage": debt.repayment_progress_percentage,
                        "debt_tag": debt.debt_tag.name,
                    },
                }
            )
        except Exception as e:
            return JsonResponse(
                {"success": False, "error": f"Error creating debt: {str(e)}"}, status=400
            )


class DebtUpdateView(LoginRequiredView):
    """View for updating debts via AJAX."""

    def post(self, request, *args, **kwargs):
        debt_id = request.POST.get("debt_id")
        name = request.POST.get("name")
        description = request.POST.get("description", "")
        total_amount = request.POST.get("total_amount")

        if not debt_id or not name or not total_amount:
            return JsonResponse(
                {"success": False, "error": "Debt ID, name, and total amount are required"},
                status=400,
            )

        try:
            total_amount = Decimal(total_amount)
            if total_amount <= 0:
                return JsonResponse(
                    {"success": False, "error": "Total amount must be greater than zero"},
                    status=400,
                )

            debt = get_object_or_404(Debt, id=debt_id, user=request.user)
            debt.name = name
            debt.description = description
            debt.total_amount = total_amount
            debt.save()

            return JsonResponse(
                {
                    "success": True,
                    "message": f'Debt "{name}" updated successfully!',
                    "debt": {
                        "id": debt.id,
                        "name": debt.name,
                        "description": debt.description,
                        "total_amount": str(debt.total_amount),
                        "borrowed_amount": str(debt.borrowed_amount),
                        "repaid_amount": str(debt.repaid_amount),
                        "remaining_to_repay": str(debt.remaining_to_repay),
                        "progress_percentage": debt.progress_percentage,
                        "repayment_progress_percentage": debt.repayment_progress_percentage,
                    },
                }
            )
        except Exception as e:
            return JsonResponse(
                {"success": False, "error": f"Error updating debt: {str(e)}"}, status=400
            )


class DebtDeleteView(LoginRequiredView):
    """View for deleting debts via AJAX."""

    def post(self, request, *args, **kwargs):
        debt_id = request.POST.get("debt_id")

        if not debt_id:
            return JsonResponse({"success": False, "error": "Debt ID is required"}, status=400)

        try:
            debt = get_object_or_404(Debt, id=debt_id, user=request.user)
            debt_name = debt.name

            # Check if debt has any transactions
            if debt.transactions.exists():
                return JsonResponse(
                    {
                        "success": False,
                        "error": (
                            f'Cannot delete debt "{debt_name}" because it has borrowing '
                            "transactions. Delete the transactions first."
                        ),
                    },
                    status=400,
                )

            debt.delete()

            return JsonResponse(
                {
                    "success": True,
                    "message": f'Debt "{debt_name}" deleted successfully!',
                    "debt_id": debt_id,
                }
            )
        except Exception as e:
            return JsonResponse(
                {"success": False, "error": f"Error deleting debt: {str(e)}"}, status=400
            )


class DebtBorrowingView(LoginRequiredView):
    """View for adding borrowing transactions via AJAX."""

    def post(self, request, *args, **kwargs):
        debt_id = request.POST.get("debt_id")
        amount = request.POST.get("amount")
        date = request.POST.get("date")
        notes = request.POST.get("notes", "")

        if not debt_id or not amount or not date:
            return JsonResponse(
                {"success": False, "error": "Debt ID, amount, and date are required"}, status=400
            )

        try:
            amount = Decimal(amount)
            if amount <= 0:
                return JsonResponse(
                    {"success": False, "error": "Amount must be greater than zero"}, status=400
                )

            # Parse the date string to a date object
            try:
                parsed_date = datetime.strptime(date, "%Y-%m-%d").date()
            except ValueError:
                return JsonResponse(
                    {"success": False, "error": "Invalid date format. Use YYYY-MM-DD"}, status=400
                )

            debt = get_object_or_404(Debt, id=debt_id)

            # Check if this would exceed total amount
            current_borrowed = debt.borrowed_amount
            if current_borrowed + amount > debt.total_amount:
                return JsonResponse(
                    {
                        "success": False,
                        "error": (
                            f"This borrowing would exceed the total debt amount of "
                            f"{debt.total_amount}"
                        ),
                    },
                    status=400,
                )

            transaction = DebtTransaction.objects.create(
                debt=debt, amount=amount, date=parsed_date, notes=notes
            )

            # Recalculate borrowed amount from transactions
            debt.recalculate_borrowed_amount()

            return JsonResponse(
                {
                    "success": True,
                    "message": f'Added {amount} borrowing to "{debt.name}"',
                    "transaction": {
                        "id": transaction.id,
                        "amount": str(transaction.amount),
                        "date": transaction.date.strftime("%Y-%m-%d"),
                        "date_iso": transaction.date.strftime("%Y-%m-%d"),
                        "notes": transaction.notes,
                        "notes_escaped": (
                            transaction.notes.replace("'", "\\'") if transaction.notes else ""
                        ),
                        "created_at": transaction.created_at.strftime("%Y-%m-%d"),
                    },
                    "debt": {
                        "name": debt.name,
                        "total_amount": str(debt.total_amount),
                        "borrowed_amount": str(debt.borrowed_amount),
                        "repaid_amount": str(debt.repaid_amount),
                        "remaining_to_repay": str(debt.remaining_to_repay),
                        "progress_percentage": debt.progress_percentage,
                        "repayment_progress_percentage": debt.repayment_progress_percentage,
                    },
                }
            )
        except Exception as e:
            return JsonResponse(
                {"success": False, "error": f"Error adding borrowing: {str(e)}"}, status=400
            )


class DebtTransactionUpdateView(LoginRequiredView):
    """View for updating borrowing transactions via AJAX."""

    def post(self, request, *args, **kwargs):
        transaction_id = request.POST.get("transaction_id")
        debt_id = request.POST.get("debt_id")
        amount = request.POST.get("amount")
        date = request.POST.get("date")
        notes = request.POST.get("notes", "")

        if not transaction_id or not debt_id or not amount or not date:
            return JsonResponse(
                {
                    "success": False,
                    "error": "Transaction ID, debt ID, amount, and date are required",
                },
                status=400,
            )

        try:
            amount = Decimal(amount)
            if amount <= 0:
                return JsonResponse(
                    {"success": False, "error": "Amount must be greater than zero"}, status=400
                )

            # Parse the date string to a date object
            try:
                parsed_date = datetime.strptime(date, "%Y-%m-%d").date()
            except ValueError:
                return JsonResponse(
                    {"success": False, "error": "Invalid date format. Use YYYY-MM-DD"}, status=400
                )

            transaction = get_object_or_404(DebtTransaction, id=transaction_id, debt_id=debt_id)
            debt = transaction.debt

            # Update transaction
            transaction.amount = amount
            transaction.date = parsed_date
            transaction.notes = notes
            transaction.save()

            # Recalculate borrowed amount from transactions
            debt.recalculate_borrowed_amount()

            return JsonResponse(
                {
                    "success": True,
                    "message": f'Updated borrowing transaction for "{debt.name}"',
                    "transaction": {
                        "id": transaction.id,
                        "amount": str(transaction.amount),
                        "date": transaction.date.strftime("%Y-%m-%d"),
                        "date_iso": transaction.date.strftime("%Y-%m-%d"),
                        "notes": transaction.notes,
                        "notes_escaped": (
                            transaction.notes.replace("'", "\\'") if transaction.notes else ""
                        ),
                        "created_at": transaction.created_at.strftime("%Y-%m-%d"),
                    },
                    "debt": {
                        "name": debt.name,
                        "total_amount": str(debt.total_amount),
                        "borrowed_amount": str(debt.borrowed_amount),
                        "repaid_amount": str(debt.repaid_amount),
                        "remaining_to_repay": str(debt.remaining_to_repay),
                        "progress_percentage": debt.progress_percentage,
                        "repayment_progress_percentage": debt.repayment_progress_percentage,
                    },
                }
            )
        except Exception as e:
            return JsonResponse(
                {"success": False, "error": f"Error updating transaction: {str(e)}"}, status=400
            )


class DebtTransactionDeleteView(LoginRequiredView):
    """View for deleting borrowing transactions via AJAX."""

    def post(self, request, *args, **kwargs):
        transaction_id = request.POST.get("transaction_id")

        if not transaction_id:
            return JsonResponse(
                {"success": False, "error": "Transaction ID is required"}, status=400
            )

        try:
            transaction = get_object_or_404(DebtTransaction, id=transaction_id)
            debt = transaction.debt
            transaction_amount = transaction.amount

            # Delete the transaction
            transaction.delete()

            # Recalculate borrowed amount from transactions
            debt.recalculate_borrowed_amount()

            return JsonResponse(
                {
                    "success": True,
                    "message": f'Deleted borrowing transaction of {transaction_amount} from "{debt.name}"',  # noqa: E501
                    "debt": {
                        "name": debt.name,
                        "total_amount": str(debt.total_amount),
                        "borrowed_amount": str(debt.borrowed_amount),
                        "repaid_amount": str(debt.repaid_amount),
                        "remaining_to_repay": str(debt.remaining_to_repay),
                        "progress_percentage": debt.progress_percentage,
                        "repayment_progress_percentage": debt.repayment_progress_percentage,
                    },
                }
            )
        except Exception as e:
            return JsonResponse(
                {"success": False, "error": f"Error deleting transaction: {str(e)}"}, status=400
            )
