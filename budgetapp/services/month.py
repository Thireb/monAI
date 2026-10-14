"""Figures for one budget month: lines, accounts, daily spending and Safe to spend today.

Money rules (the same as ``Budget`` in ``budgetapp/models.py``):

- A line's ``spent`` is the sum of its sub-expenses that are not returns.
- A return moves money from the line back to the budget, so it also uses up the line:
  ``left = amount - spent - returned``.
- ``unallocated`` is ``Budget.get_remaining_budget()``: income - lines + returns.

Safe to spend today uses only the lines marked ``is_daily``:

- ``allowance`` = (what is left on daily lines at the start of today) / (days left, today
  included).
- ``safe_today`` = ``allowance`` - (what was spent on daily lines today). It is negative when
  today's spending is over the allowance.
"""

from __future__ import annotations

import calendar
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from django.db.models import Q, Sum
from django.db.models.functions import Coalesce
from django.utils import timezone

from budgetapp.models import Budget, Expense, SubExpense

ZERO = Decimal("0")
CENT = Decimal("0.01")
NO_ACCOUNT_COLOR = "#9AA49E"
NO_CATEGORY_COLOR = "#B9C4BD"

# A line is "close" to its limit from this share of use.
CLOSE_PERCENT = 75


def _pct(part: Decimal, whole: Decimal) -> int:
    """Return ``part / whole`` as a whole percent, limited to 0..100."""
    if whole <= 0:
        return 100 if part > 0 else 0
    value = int((part / whole * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    return max(0, min(100, value))


def _status(amount: Decimal, used: Decimal) -> str:
    """Classify use of an amount: ``ok``, ``close``, ``done`` or ``over``."""
    if used > amount:
        return "over"
    if amount > 0 and used == amount:
        return "done"
    if _pct(used, amount) >= CLOSE_PERCENT:
        return "close"
    return "ok"


@dataclass(frozen=True)
class LineView:
    """One expense line of the month."""

    id: int
    name: str
    amount: Decimal
    spent: Decimal
    returned: Decimal
    left: Decimal
    used_pct: int
    status: str
    is_daily: bool
    is_recurring: bool
    category_name: str
    category_color: str
    account_id: int | None
    account_name: str
    account_color: str


@dataclass(frozen=True)
class CategoryGroup:
    """Lines of one category, with totals."""

    name: str
    color: str
    amount: Decimal
    left: Decimal
    lines: list[LineView]


@dataclass(frozen=True)
class AccountView:
    """One account tag: its allocation after transfers and how much of it is used."""

    tag_id: int
    name: str
    color: str
    total: Decimal
    used: Decimal
    used_pct: int
    status: str


@dataclass(frozen=True)
class DayBar:
    """Daily spending on day-to-day lines, for the day-by-day chart."""

    day: int
    label: str
    spent: Decimal
    height_pct: int
    is_over: bool
    is_today: bool
    is_future: bool


@dataclass(frozen=True)
class MonthSnapshot:
    """Everything the month pages show, computed once."""

    budget: Budget
    income: Decimal
    gross: Decimal
    returns: Decimal
    spent: Decimal
    unallocated: Decimal
    allocated_pct: int
    lines: list[LineView]
    categories: list[CategoryGroup]
    accounts: list[AccountView]
    is_current: bool
    days_in_month: int
    days_left: int
    has_daily_lines: bool
    daily_amount: Decimal
    daily_left: Decimal
    daily_limit: Decimal
    spent_today: Decimal
    allowance_today: Decimal | None
    safe_today: Decimal | None
    days: list[DayBar] = field(default_factory=list)
    limit_line_pct: int = 0
    streak: int = 0
    recent_days: list[DayBar] = field(default_factory=list)

    @property
    def over_today(self) -> Decimal:
        """How much today's spending is over the allowance (0 when it is not)."""
        if self.safe_today is None or self.safe_today >= 0:
            return ZERO
        return -self.safe_today


def _line_rows(budget: Budget) -> list[LineView]:
    """Build the line views with 1 query, ordered with day-to-day lines first."""
    expenses = (
        Expense.objects.filter(budget=budget)
        .select_related("category", "tag_foreign_key")
        .annotate(
            spent_sum=Coalesce(
                Sum("sub_expenses__amount", filter=Q(sub_expenses__is_return=False)), ZERO
            ),
            returned_sum=Coalesce(
                Sum("sub_expenses__amount", filter=Q(sub_expenses__is_return=True)), ZERO
            ),
        )
        .order_by("-is_daily", "category__name", "name", "id")
    )
    rows = []
    for e in expenses:
        spent = Decimal(e.spent_sum)
        returned = Decimal(e.returned_sum)
        used = spent + returned
        tag = e.tag_foreign_key
        rows.append(
            LineView(
                id=e.id,
                name=e.name,
                amount=e.amount,
                spent=spent,
                returned=returned,
                left=e.amount - used,
                used_pct=_pct(used, e.amount),
                status=_status(e.amount, used),
                is_daily=e.is_daily,
                is_recurring=e.is_recurring,
                category_name=e.category.name if e.category else "Uncategorized",
                category_color=e.category.color if e.category else NO_CATEGORY_COLOR,
                account_id=tag.id if tag else None,
                account_name=tag.name if tag else "No account",
                account_color=tag.color if tag else NO_ACCOUNT_COLOR,
            )
        )
    return rows


def _category_groups(lines: list[LineView]) -> list[CategoryGroup]:
    """Group lines by category, largest category first."""
    grouped: dict[str, list[LineView]] = defaultdict(list)
    for line in lines:
        grouped[line.category_name].append(line)
    groups = [
        CategoryGroup(
            name=name,
            color=items[0].category_color,
            amount=sum((i.amount for i in items), ZERO),
            left=sum((i.left for i in items), ZERO),
            lines=items,
        )
        for name, items in grouped.items()
    ]
    return sorted(groups, key=lambda g: (-g.amount, g.name))


def _accounts(budget: Budget, lines: list[LineView]) -> list[AccountView]:
    """Account tags with their allocation (after transfers) and their use."""
    used_by_tag: dict[int, Decimal] = defaultdict(lambda: ZERO)
    for line in lines:
        if line.account_id is not None:
            used_by_tag[line.account_id] += line.spent + line.returned
    accounts = []
    for data in budget.get_tag_account_breakdown().values():
        total = Decimal(data["amount"])
        used = used_by_tag[data["tag_id"]]
        if total == 0 and used == 0:
            continue
        accounts.append(
            AccountView(
                tag_id=data["tag_id"],
                name=data["label"],
                color=data["color"],
                total=total,
                used=used,
                used_pct=_pct(used, total),
                status=_status(total, used),
            )
        )
    return sorted(accounts, key=lambda a: (-a.total, a.name))


def _daily_spend_by_day(budget: Budget) -> dict[int, Decimal]:
    """Spending on day-to-day lines per day of the month (returns excluded)."""
    subs = SubExpense.objects.filter(
        expense__budget=budget, expense__is_daily=True, is_return=False
    ).only("amount", "created_at")
    by_day: dict[int, Decimal] = defaultdict(lambda: ZERO)
    for sub in subs:
        local = timezone.localtime(sub.created_at).date()
        if local.year == budget.month.year and local.month == budget.month.month:
            by_day[local.day] += sub.amount
    return by_day


def _streak(by_day: dict[int, Decimal], limit: Decimal, today_day: int) -> int:
    """Days in a row, ending today, with daily spending at or under ``limit``.

    Counting starts at the first day with a recorded spend, so days before the
    user began to record do not count.
    """
    if limit <= 0 or not by_day:
        return 0
    first = min(by_day)
    streak = 0
    for day in range(today_day, first - 1, -1):
        if by_day.get(day, ZERO) > limit:
            break
        streak += 1
    return streak


def build_month_snapshot(budget: Budget, today: date | None = None) -> MonthSnapshot:
    """Compute all figures for ``budget``. ``today`` defaults to the local date."""
    today = today or timezone.localdate()
    lines = _line_rows(budget)
    income = budget.income
    gross = sum((line.amount for line in lines), ZERO)
    returns = sum((line.returned for line in lines), ZERO)
    spent = sum((line.spent for line in lines), ZERO)
    unallocated = income - gross + returns

    month = budget.month
    days_in_month = calendar.monthrange(month.year, month.month)[1]
    is_current = (today.year, today.month) == (month.year, month.month)
    days_left = days_in_month - today.day + 1 if is_current else 0

    daily_lines = [line for line in lines if line.is_daily]
    daily_amount = sum((line.amount for line in daily_lines), ZERO)
    daily_left = sum((line.left for line in daily_lines), ZERO)
    daily_limit = (daily_amount / days_in_month).quantize(CENT, rounding=ROUND_HALF_UP)

    by_day = _daily_spend_by_day(budget)
    spent_today = by_day.get(today.day, ZERO) if is_current else ZERO
    allowance_today: Decimal | None = None
    safe_today: Decimal | None = None
    if is_current and daily_lines:
        allowance_today = ((daily_left + spent_today) / days_left).quantize(
            CENT, rounding=ROUND_HALF_UP
        )
        safe_today = allowance_today - spent_today

    # The limit line sits at 80 % height unless a day spent more.
    scale = (
        max([daily_limit * Decimal("1.25"), *by_day.values()]) if by_day or daily_limit else ZERO
    )
    days = [
        DayBar(
            day=d,
            label=date(month.year, month.month, d).strftime("%a")[:2],
            spent=by_day.get(d, ZERO),
            height_pct=_pct(by_day.get(d, ZERO), scale),
            is_over=daily_limit > 0 and by_day.get(d, ZERO) > daily_limit,
            is_today=is_current and d == today.day,
            is_future=is_current and d > today.day,
        )
        for d in range(1, days_in_month + 1)
    ]

    return MonthSnapshot(
        budget=budget,
        income=income,
        gross=gross,
        returns=returns,
        spent=spent,
        unallocated=unallocated,
        allocated_pct=_pct(gross - returns, income),
        lines=lines,
        categories=_category_groups(lines),
        accounts=_accounts(budget, lines),
        is_current=is_current,
        days_in_month=days_in_month,
        days_left=days_left,
        has_daily_lines=bool(daily_lines),
        daily_amount=daily_amount,
        daily_left=daily_left,
        daily_limit=daily_limit,
        spent_today=spent_today,
        allowance_today=allowance_today,
        safe_today=safe_today,
        days=days,
        limit_line_pct=_pct(daily_limit, scale),
        streak=_streak(by_day, daily_limit, today.day) if is_current else 0,
        recent_days=[bar for bar in days if not bar.is_future][-7:] if is_current else [],
    )
