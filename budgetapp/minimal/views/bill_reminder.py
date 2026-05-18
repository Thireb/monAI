"""
Bill reminder management (minimal UI) and AJAX defaults for expense modal.
"""

from datetime import datetime
from decimal import Decimal

from django.http import JsonResponse
from django.shortcuts import get_object_or_404

from budgetapp.bill_reminder_utils import reminder_defaults_for_expense
from budgetapp.models import BillReminder, Category, Tag

from .base import LoginRequiredTemplateView, LoginRequiredView


class BillReminderListView(LoginRequiredTemplateView):
    """Page to list and edit scheduled bills."""

    template_name = "minimal/bill_reminders/bill_reminder_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context["bill_reminders"] = BillReminder.objects.filter(user=user).order_by(
            "next_bill_date", "name"
        )
        context["categories"] = Category.objects.filter(user=user).order_by("name")
        context["tags"] = Tag.objects.filter(user=user).order_by("name")
        context["severity_choices"] = BillReminder.Severity.choices
        return context


class BillReminderSaveView(LoginRequiredView):
    """Create or update a bill reminder via POST."""

    def post(self, request, *args, **kwargs):
        rid = request.POST.get("reminder_id")
        name = (request.POST.get("name") or "").strip()
        amount_raw = request.POST.get("amount", "0")
        next_raw = request.POST.get("next_bill_date")
        days_raw = request.POST.get("remind_days_before", "30")
        severity = request.POST.get("severity") or BillReminder.Severity.MEDIUM
        rec_raw = request.POST.get("recurrence_months", "12")
        notes = request.POST.get("notes", "")
        category_id = request.POST.get("category") or None
        tag_id = request.POST.get("tag") or None
        is_active = request.POST.get("is_active") == "on"

        if not name:
            return JsonResponse({"status": "error", "message": "Name is required"}, status=400)
        try:
            amount = Decimal(amount_raw)
        except Exception:
            return JsonResponse({"status": "error", "message": "Invalid amount"}, status=400)
        if amount < 0:
            return JsonResponse(
                {"status": "error", "message": "Amount cannot be negative"},
                status=400,
            )
        if not next_raw:
            return JsonResponse(
                {"status": "error", "message": "Next due date is required"},
                status=400,
            )
        try:
            next_bill_date = datetime.strptime(next_raw, "%Y-%m-%d").date()
        except ValueError:
            return JsonResponse({"status": "error", "message": "Invalid date format"}, status=400)

        sev_values = {c[0] for c in BillReminder.Severity.choices}
        if severity not in sev_values:
            severity = BillReminder.Severity.MEDIUM

        try:
            remind_days_before = max(1, int(days_raw))
        except ValueError:
            remind_days_before = 30
        try:
            recurrence_months = max(1, int(rec_raw))
        except ValueError:
            recurrence_months = 12

        if category_id and not Category.objects.filter(pk=category_id, user=request.user).exists():
            return JsonResponse({"status": "error", "message": "Unknown category"}, status=400)
        if tag_id and not Tag.objects.filter(pk=tag_id, user=request.user).exists():
            return JsonResponse({"status": "error", "message": "Unknown tag"}, status=400)

        if rid:
            reminder = get_object_or_404(BillReminder, pk=rid, user=request.user)
        else:
            reminder = BillReminder(user=request.user)

        reminder.name = name
        reminder.amount = amount
        reminder.next_bill_date = next_bill_date
        reminder.remind_days_before = remind_days_before
        reminder.severity = severity
        reminder.recurrence_months = recurrence_months
        reminder.notes = notes
        reminder.is_active = is_active
        reminder.category_id = category_id
        reminder.tag_id = tag_id
        reminder.save()

        return JsonResponse(
            {
                "status": "success",
                "message": "Bill reminder saved",
                "reminder": {
                    "id": reminder.id,
                    "name": reminder.name,
                    "amount": str(reminder.amount),
                    "next_bill_date": reminder.next_bill_date.isoformat(),
                    "remind_days_before": reminder.remind_days_before,
                    "severity": reminder.severity,
                    "recurrence_months": reminder.recurrence_months,
                    "is_active": reminder.is_active,
                    "notes": reminder.notes,
                    "category_id": reminder.category_id,
                    "tag_id": reminder.tag_id,
                },
            }
        )


class BillReminderDeleteView(LoginRequiredView):
    """Delete a bill reminder."""

    def post(self, request, *args, **kwargs):
        rid = request.POST.get("reminder_id")
        if not rid:
            return JsonResponse({"status": "error", "message": "reminder_id required"}, status=400)
        reminder = get_object_or_404(BillReminder, pk=rid, user=request.user)
        reminder.delete()
        return JsonResponse({"status": "success", "message": "Reminder deleted"})


class BillReminderDefaultsView(LoginRequiredView):
    """GET JSON for expense modal when next due date changes (live defaults)."""

    def get(self, request, *args, **kwargs):
        expense_id = request.GET.get("expense_id")
        next_raw = request.GET.get("next_bill_date")
        expense = None
        if expense_id:
            from budgetapp.models import Expense

            expense = (
                Expense.objects.filter(pk=expense_id, budget__user=request.user)
                .select_related("bill_reminder")
                .first()
            )
        next_date = None
        if next_raw:
            try:
                next_date = datetime.strptime(next_raw, "%Y-%m-%d").date()
            except ValueError:
                pass
        data = reminder_defaults_for_expense(
            user=request.user,
            expense=expense,
            next_bill_date=next_date,
        )
        return JsonResponse(data)
