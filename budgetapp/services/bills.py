"""Bills of one month, for the bill timeline on the month page.

A bill reminder becomes a line of the month it is due in (``apply_bill_reminders_to_budget``),
and its ``next_bill_date`` then moves forward by ``recurrence_months``. So the bills of a month
are:

- its lines that are linked to a reminder (the due date is ``next_bill_date`` moved back by
  ``recurrence_months``, when that falls in the month), and
- active reminders due in the month that are not lines yet (``line_id`` is ``None``).

A bill is paid when its line has nothing left (``left <= 0``).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from dateutil.relativedelta import relativedelta

from budgetapp.models import BillReminder, Budget
from budgetapp.services.month import MonthSnapshot

# A bill due in this many days or fewer is "soon".
SOON_DAYS = 7


@dataclass(frozen=True)
class MonthBill:
    """One bill of the month."""

    name: str
    amount: Decimal
    due: date | None
    days_until: int | None
    line_id: int | None
    is_paid: bool
    state: str  # paid, late, today, soon, later, unplanned


def bill_state(is_paid: bool, line_id: int | None, days_until: int | None) -> str:
    """Classify a bill for its badge colour."""
    if is_paid:
        return "paid"
    if line_id is None:
        return "unplanned"
    if days_until is None:
        return "later"
    if days_until < 0:
        return "late"
    if days_until == 0:
        return "today"
    return "soon" if days_until <= SOON_DAYS else "later"


def month_bills(budget: Budget, snap: MonthSnapshot, today: date) -> list[MonthBill]:
    """Return the bills of ``budget``'s month, by due date (bills without a day last)."""
    left_by_line = {line.id: line.left for line in snap.lines}
    bills: list[MonthBill] = []
    linked = budget.expenses.filter(bill_reminder__isnull=False).select_related("bill_reminder")
    applied_ids = set()
    for line in linked:
        reminder = line.bill_reminder
        applied_ids.add(reminder.id)
        due: date | None = reminder.next_bill_date - relativedelta(
            months=reminder.recurrence_months
        )
        if due is not None and (due.year, due.month) != (budget.month.year, budget.month.month):
            due = None
        is_paid = left_by_line.get(line.id, line.amount) <= 0 and line.amount > 0
        days = (due - today).days if due else None
        state = bill_state(is_paid, line.id, days)
        bills.append(MonthBill(line.name, line.amount, due, days, line.id, is_paid, state))
    pending = BillReminder.objects.filter(
        user=budget.user,
        is_active=True,
        next_bill_date__year=budget.month.year,
        next_bill_date__month=budget.month.month,
    ).exclude(id__in=applied_ids)
    for reminder in pending:
        days = (reminder.next_bill_date - today).days
        bills.append(
            MonthBill(
                reminder.name,
                reminder.amount,
                reminder.next_bill_date,
                days,
                None,
                False,
                "unplanned",
            )
        )
    return sorted(bills, key=lambda b: (b.due is None, b.due or date.max, b.name))


def coming_up(budget: Budget, snap: MonthSnapshot, today: date, limit: int = 4) -> list[MonthBill]:
    """Bills for the home page: unpaid bills of this month, then reminders of later months."""
    unpaid = [bill for bill in month_bills(budget, snap, today) if not bill.is_paid]
    # A reminder that is a line of this month already shows above, so skip its next date.
    in_month = budget.expenses.filter(bill_reminder__isnull=False).values("bill_reminder")
    later = (
        BillReminder.objects.filter(
            user=budget.user,
            is_active=True,
            next_bill_date__gte=budget.month + relativedelta(months=1),
        )
        .exclude(id__in=in_month)
        .order_by("next_bill_date", "name")[: max(0, limit - len(unpaid))]
    )
    for reminder in later:
        days = (reminder.next_bill_date - today).days
        unpaid.append(
            MonthBill(
                reminder.name,
                reminder.amount,
                reminder.next_bill_date,
                days,
                None,
                False,
                bill_state(False, reminder.id, days),
            )
        )
    return unpaid[:limit]
