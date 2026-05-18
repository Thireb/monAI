"""
Bill reminder scheduling: dashboard banner window and budget auto-line items.
"""

from __future__ import annotations

from datetime import date

from dateutil.relativedelta import relativedelta

from budgetapp.models import BillReminder, Budget, Expense


def reminder_start_date(reminder: BillReminder) -> date:
    """First calendar day the user should start seeing the reminder."""
    return reminder.next_bill_date - relativedelta(days=reminder.remind_days_before)


def billing_month_start(reminder: BillReminder) -> date:
    """First day of the month that contains the due date."""
    d = reminder.next_bill_date
    return date(d.year, d.month, 1)


def should_show_dashboard_banner(reminder: BillReminder, today: date) -> bool:
    """
    Banner is visible from remind_days_before through the day before the billing
    month begins (first day of due month hides it).
    """
    if not reminder.is_active:
        return False
    start = reminder_start_date(reminder)
    bill_month = billing_month_start(reminder)
    return start <= today < bill_month


def dashboard_banner_reminders_for_user(user, today: date) -> list[BillReminder]:
    """Active reminders that should show on the minimal home dashboard."""
    qs = BillReminder.objects.filter(user=user, is_active=True).order_by(
        "next_bill_date", "name"
    )
    return [r for r in qs if should_show_dashboard_banner(r, today)]


def reminder_matches_budget_month(reminder: BillReminder, budget_month: date) -> bool:
    """True if the due date falls in the same calendar month as the budget."""
    due = reminder.next_bill_date
    return due.year == budget_month.year and due.month == budget_month.month


def advance_next_bill_date(reminder: BillReminder) -> None:
    """Roll the due date forward by recurrence_months (typically 12 for annual)."""
    reminder.next_bill_date += relativedelta(months=reminder.recurrence_months)
    reminder.save(update_fields=["next_bill_date", "updated_at"])


def apply_bill_reminders_to_budget(budget: Budget) -> int:
    """
    For each active reminder due in this budget month, create a linked expense
    if none exists yet, then advance the reminder's next due date.
    Returns the number of expenses created.
    """
    user = budget.user
    if user is None:
        return 0
    created = 0
    month_start = budget.month.replace(day=1)
    candidates = BillReminder.objects.filter(user=user, is_active=True)
    for reminder in candidates:
        if not reminder_matches_budget_month(reminder, month_start):
            continue
        exists = Expense.objects.filter(budget=budget, bill_reminder=reminder).exists()
        if exists:
            continue
        Expense.objects.create(
            budget=budget,
            name=reminder.name,
            amount=reminder.amount,
            is_recurring=False,
            category_id=reminder.category_id,
            tag_foreign_key_id=reminder.tag_id,
            bill_reminder=reminder,
        )
        advance_next_bill_date(reminder)
        created += 1
    return created


def sync_expense_bill_reminder(
    *,
    user,
    expense: Expense,
    enabled: bool,
    next_bill_date: date | None,
    remind_days_before: int,
    severity: str,
    recurrence_months: int,
) -> None:
    """
    Attach, update, or detach a BillReminder from an expense based on optional form data.
    """
    if not enabled:
        expense.bill_reminder = None
        expense.save(update_fields=["bill_reminder", "updated_at"])
        return
    if next_bill_date is None:
        return
    if expense.bill_reminder_id:
        br = BillReminder.objects.get(pk=expense.bill_reminder_id, user=user)
    else:
        br = BillReminder(user=user)
    br.name = expense.name
    br.amount = expense.amount
    br.category_id = expense.category_id
    br.tag_id = expense.tag_foreign_key_id
    br.next_bill_date = next_bill_date
    br.remind_days_before = max(1, int(remind_days_before))
    br.severity = severity
    br.recurrence_months = max(1, int(recurrence_months))
    br.is_active = True
    br.save()
    expense.bill_reminder = br
    expense.save(update_fields=["bill_reminder", "updated_at"])


def reminder_defaults_for_expense(
    *,
    user,
    expense: Expense | None,
    next_bill_date: date | None,
) -> dict:
    """JSON-friendly defaults for the expense modal (live refresh)."""
    if expense and expense.bill_reminder_id:
        br = BillReminder.objects.filter(pk=expense.bill_reminder_id, user=user).first()
        if br:
            return {
                "has_reminder": True,
                "reminder_id": br.id,
                "next_bill_date": (
                    next_bill_date.isoformat()
                    if next_bill_date
                    else br.next_bill_date.isoformat()
                ),
                "remind_days_before": br.remind_days_before,
                "severity": br.severity,
                "recurrence_months": br.recurrence_months,
            }
    return {
        "has_reminder": False,
        "reminder_id": None,
        "next_bill_date": next_bill_date.isoformat() if next_bill_date else "",
        "remind_days_before": 30,
        "severity": BillReminder.Severity.MEDIUM,
        "recurrence_months": 12,
    }
