"""
Expense CRUD views.
"""

from decimal import Decimal

from django.contrib.humanize.templatetags.humanize import intcomma
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone

from budgetapp.models import Budget, Expense

from .base import LoginRequiredView, UnicodeJsonResponse


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
        budget = get_object_or_404(Budget, month=budget_date, user=self.request.user)

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
        budget = get_object_or_404(Budget, month=budget_date, user=self.request.user)

        expense_id = request.POST.get("expense_id")
        if expense_id:
            try:
                expense = get_object_or_404(Expense, id=expense_id, budget=budget)
                expense_name = expense.name
                expense_amount = float(expense.amount)
                expense.delete()

                displays = budget.get_summary_display_strings(
                    lambda v: intcomma(f"{float(v):,.2f}")
                )

                return JsonResponse(
                    {
                        "status": "success",
                        "message": f'Expense "{expense_name}" deleted successfully!',
                        "expense_id": expense_id,
                        "deleted_amount": expense_amount,
                        "new_gross_expenses_display": displays["gross_expenses_display"],
                        "new_total_returns_display": displays["total_returns_display"],
                        "new_net_expenses_display": displays["net_expenses_display"],
                        "new_remaining_budget_display": displays["remaining_budget_display"],
                    }
                )
            except Exception as e:
                return JsonResponse(
                    {"status": "error", "message": f"Error deleting expense: {str(e)}"}, status=400
                )

        return JsonResponse({"status": "error", "message": "No expense ID provided"}, status=400)
