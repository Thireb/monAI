"""
Expense CRUD views.
"""

from datetime import datetime
from decimal import Decimal

from django.contrib.humanize.templatetags.humanize import intcomma
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone

from budgetapp.bill_reminder_utils import sync_expense_bill_reminder
from budgetapp.models import BillReminder, Budget, Expense

from .base import LoginRequiredView, UnicodeJsonResponse


class ExpenseCreateUpdateView(LoginRequiredView):
    """Class-based view for creating or updating expenses."""

    def _format_currency(self, val: float) -> str:
        """Format a float value as a string with comma
        as thousands separator and two decimal places."""
        return intcomma(f"{val:,.2f}")

    def _expense_tag_json(self, expense: Expense) -> dict:
        return {
            "id": expense.tag_foreign_key.id if expense.tag_foreign_key else None,
            "name": expense.tag_foreign_key.name if expense.tag_foreign_key else None,
            "color": expense.tag_foreign_key.color if expense.tag_foreign_key else None,
        }

    def _bill_reminder_json(self, expense: Expense) -> dict | None:
        if not expense.bill_reminder_id:
            return None
        br = expense.bill_reminder
        return {
            "id": br.id,
            "next_bill_date": br.next_bill_date.isoformat(),
            "remind_days_before": br.remind_days_before,
            "severity": br.severity,
            "recurrence_months": br.recurrence_months,
        }

    def _expense_response_dict(self, expense: Expense) -> dict:
        category_name = expense.category.name if expense.category else "Uncategorized"
        category_color = expense.category.color if expense.category else "#e0e0e0"
        sub_expenses = []
        return {
            "id": expense.id,
            "name": expense.name,
            "amount": float(expense.amount),
            "amount_display": self._format_currency(expense.amount),
            "is_recurring": expense.is_recurring,
            "category_id": expense.category_id,
            "category_name": category_name,
            "category_color": category_color,
            "tag_foreign_key_id": expense.tag_foreign_key_id,
            "tag_foreign_key": self._expense_tag_json(expense),
            "sub_expenses": sub_expenses,
            "sub_expenses_exists": expense.sub_expenses.exists(),
            "bill_reminder": self._bill_reminder_json(expense),
            "bill_reminder_id": expense.bill_reminder_id,
        }

    def _parse_reminder_from_post(self, request):
        enabled = request.POST.get("bill_reminder_enabled") == "on"
        next_raw = request.POST.get("bill_reminder_next_date", "").strip()
        next_date = None
        if next_raw:
            try:
                next_date = datetime.strptime(next_raw, "%Y-%m-%d").date()
            except ValueError:
                next_date = None
        try:
            days_before = int(request.POST.get("bill_reminder_days_before", "30"))
        except ValueError:
            days_before = 30
        severity = request.POST.get("bill_reminder_severity") or BillReminder.Severity.MEDIUM
        sev_values = {c[0] for c in BillReminder.Severity.choices}
        if severity not in sev_values:
            severity = BillReminder.Severity.MEDIUM
        try:
            recurrence = int(request.POST.get("bill_reminder_recurrence_months", "12"))
        except ValueError:
            recurrence = 12
        return enabled, next_date, days_before, severity, recurrence

    def post(self, request, *args, **kwargs):
        year = kwargs.get("year")
        month = kwargs.get("month")
        budget_date = timezone.datetime(year=year, month=month, day=1).date()
        budget = get_object_or_404(Budget, month=budget_date, is_archived=False, user=self.request.user)

        expense_id = request.POST.get("expense_id")
        name = request.POST.get("name")
        amount = request.POST.get("amount")
        is_recurring = request.POST.get("is_recurring") == "on"
        category_id = request.POST.get("category")
        tag_id = request.POST.get("tag")

        (
            rem_enabled,
            rem_next,
            rem_days,
            rem_severity,
            rem_recurrence,
        ) = self._parse_reminder_from_post(request)

        def apply_reminder(expense: Expense) -> None:
            if not rem_enabled:
                sync_expense_bill_reminder(
                    user=request.user,
                    expense=expense,
                    enabled=False,
                    next_bill_date=None,
                    remind_days_before=rem_days,
                    severity=rem_severity,
                    recurrence_months=rem_recurrence,
                )
                return
            if rem_next is None:
                return
            sync_expense_bill_reminder(
                user=request.user,
                expense=expense,
                enabled=True,
                next_bill_date=rem_next,
                remind_days_before=rem_days,
                severity=rem_severity,
                recurrence_months=rem_recurrence,
            )

        try:
            if expense_id:
                expense = get_object_or_404(Expense, id=expense_id, budget=budget)
                expense.name = name
                expense.amount = Decimal(amount)
                expense.is_recurring = is_recurring
                expense.category_id = category_id if category_id else None
                expense.tag_foreign_key_id = tag_id if tag_id else None
                expense.save()
                apply_reminder(expense)
                expense.refresh_from_db()

                return UnicodeJsonResponse(
                    {
                        "status": "success",
                        "message": "Expense updated successfully!",
                        "expense": self._expense_response_dict(expense),
                        "action": "update",
                    }
                )

            expense = Expense.objects.create(
                budget=budget,
                name=name,
                amount=Decimal(amount),
                is_recurring=is_recurring,
                category_id=category_id if category_id else None,
                tag_foreign_key_id=tag_id if tag_id else None,
            )
            apply_reminder(expense)
            expense.refresh_from_db()

            return UnicodeJsonResponse(
                {
                    "status": "success",
                    "message": "Expense added successfully!",
                    "expense": self._expense_response_dict(expense),
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
        budget = get_object_or_404(Budget, month=budget_date, is_archived=False, user=self.request.user)

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
