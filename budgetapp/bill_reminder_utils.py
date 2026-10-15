"""Bill reminder scheduling: when a reminder starts, and the lines it adds to a month."""

from __future__ import annotations

from datetime import date

from dateutil.relativedelta import relativedelta

from budgetapp.models import BillReminder, Budget, Expense


def reminder_start_date(reminder: BillReminder) -> date:
    """Return the first calendar day the user should start seeing the reminder."""
    return reminder.next_bill_date - relativedelta(days=reminder.remind_days_before)


def reminder_matches_budget_month(reminder: BillReminder, budget_month: date) -> bool:
    """Return True when the due date falls in the same calendar month as the budget."""
    due = reminder.next_bill_date
    return due.year == budget_month.year and due.month == budget_month.month


def advance_next_bill_date(reminder: BillReminder) -> None:
    """Roll the due date forward by ``recurrence_months`` (typically 12 for annual bills)."""
    reminder.next_bill_date += relativedelta(months=reminder.recurrence_months)
    reminder.save(update_fields=["next_bill_date", "updated_at"])


def apply_bill_reminders_to_budget(budget: Budget) -> int:
    """Create linked expenses for reminders due in the budget month.

    For each active reminder due in this budget month, create a linked expense
    if none exists yet, then advance the reminder's next due date.

    Returns:
        Number of expenses created.
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
