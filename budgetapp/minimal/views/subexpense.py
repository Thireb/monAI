"""
SubExpense CRUD views.
"""

from decimal import Decimal

from django.contrib.humanize.templatetags.humanize import intcomma
from django.http import JsonResponse
from django.shortcuts import get_object_or_404

from budgetapp.models import Expense, SubExpense

from .base import LoginRequiredView


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
            expense = get_object_or_404(Expense, id=expense_id, budget__user=request.user)
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
            sub = get_object_or_404(
                SubExpense, id=subexpense_id, expense__budget__user=request.user
            )
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
            sub = get_object_or_404(
                SubExpense, id=subexpense_id, expense__budget__user=request.user
            )
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

