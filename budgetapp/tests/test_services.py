"""Tests for budgetapp.services: month figures, quick add and month creation."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from budgetapp.bill_reminder_utils import apply_bill_reminders_to_budget
from budgetapp.models import (
    BillReminder,
    Budget,
    Category,
    Expense,
    Goal,
    GoalContribution,
    SubExpense,
    Tag,
    TagTransfer,
)
from budgetapp.services.bills import coming_up, month_bills
from budgetapp.services.month import build_month_snapshot
from budgetapp.services.months import create_month
from budgetapp.services.quick_add import (
    QuickAddError,
    match_lines,
    parse_amount,
    parse_spend_text,
    parse_spent_at,
)
from budgetapp.services.recap import last_month_recap, month_recap

User = get_user_model()
D = Decimal


def _spend(line: Expense, amount: str, day: date, is_return: bool = False) -> SubExpense:
    """Create a sub-expense dated ``day`` (noon, local time)."""
    sub = SubExpense.objects.create(expense=line, name="x", amount=D(amount), is_return=is_return)
    when = timezone.make_aware(datetime(day.year, day.month, day.day, 12, 0))
    SubExpense.objects.filter(pk=sub.pk).update(created_at=when)
    return sub


class MonthSnapshotTests(TestCase):
    """build_month_snapshot follows the Budget money rules."""

    def setUp(self) -> None:
        self.user = User.objects.create_user(
            username="snap", email="snap@example.com", password="testpassword"
        )
        self.cash = Tag.objects.create(user=self.user, name="Cash", slug="cash", color="#2e8b57")
        self.bank = Tag.objects.create(user=self.user, name="Bank", slug="bank", color="#6b5bb5")
        food = Category.objects.create(user=self.user, name="Food", slug="food", color="#ffaa00")
        self.budget = Budget.objects.create(
            user=self.user, month=date(2026, 10, 1), income=D("10000")
        )
        self.rent = Expense.objects.create(
            budget=self.budget, name="Rent", amount=D("5000"), tag_foreign_key=self.bank
        )
        self.groceries = Expense.objects.create(
            budget=self.budget,
            name="Groceries",
            amount=D("3100"),
            is_daily=True,
            category=food,
            tag_foreign_key=self.cash,
        )

    def test_line_left_counts_spends_and_returns(self) -> None:
        _spend(self.groceries, "1000", date(2026, 10, 2))
        _spend(self.groceries, "100", date(2026, 10, 3), is_return=True)
        snap = build_month_snapshot(self.budget, today=date(2026, 10, 14))
        line = next(line for line in snap.lines if line.name == "Groceries")
        self.assertEqual(line.spent, D("1000"))
        self.assertEqual(line.returned, D("100"))
        self.assertEqual(line.left, D("2000"))
        self.assertEqual(line.status, "ok")

    def test_totals_match_budget_model(self) -> None:
        _spend(self.groceries, "250", date(2026, 10, 2), is_return=True)
        snap = build_month_snapshot(self.budget, today=date(2026, 10, 14))
        self.assertEqual(snap.gross, self.budget.get_gross_budgeted_expenses())
        self.assertEqual(snap.returns, self.budget.get_total_returns())
        self.assertEqual(snap.unallocated, self.budget.get_remaining_budget())
        self.assertEqual(snap.allocated_pct, 79)  # (8100 - 250) / 10000

    def test_line_status(self) -> None:
        _spend(self.rent, "5000", date(2026, 10, 1))
        _spend(self.groceries, "2400", date(2026, 10, 2))
        snap = build_month_snapshot(self.budget, today=date(2026, 10, 14))
        status = {line.name: line.status for line in snap.lines}
        self.assertEqual(status, {"Rent": "done", "Groceries": "close"})
        _spend(self.groceries, "1000", date(2026, 10, 3))
        snap = build_month_snapshot(self.budget, today=date(2026, 10, 14))
        line = next(line for line in snap.lines if line.name == "Groceries")
        self.assertEqual((line.status, line.left, line.used_pct), ("over", D("-300"), 100))

    def test_daily_lines_come_first(self) -> None:
        snap = build_month_snapshot(self.budget, today=date(2026, 10, 14))
        self.assertEqual([line.name for line in snap.lines], ["Groceries", "Rent"])

    def test_safe_to_spend_today(self) -> None:
        # Oct 2026 has 31 days; on the 14th there are 18 days left, today included.
        _spend(self.groceries, "1300", date(2026, 10, 5))
        _spend(self.groceries, "60", date(2026, 10, 14))
        snap = build_month_snapshot(self.budget, today=date(2026, 10, 14))
        self.assertEqual(snap.days_left, 18)
        self.assertEqual(snap.daily_left, D("1740"))
        self.assertEqual(snap.allowance_today, D("100.00"))  # (1740 + 60) / 18
        self.assertEqual(snap.safe_today, D("40.00"))
        self.assertEqual(snap.over_today, D("0"))

    def test_safe_to_spend_goes_negative_when_over(self) -> None:
        _spend(self.groceries, "250", date(2026, 10, 14))
        snap = build_month_snapshot(self.budget, today=date(2026, 10, 14))
        self.assertLess(snap.safe_today, 0)
        self.assertEqual(snap.over_today, -snap.safe_today)

    def test_no_daily_lines_means_no_safe_amount(self) -> None:
        Expense.objects.filter(pk=self.groceries.pk).update(is_daily=False)
        snap = build_month_snapshot(self.budget, today=date(2026, 10, 14))
        self.assertFalse(snap.has_daily_lines)
        self.assertIsNone(snap.safe_today)

    def test_other_month_has_no_safe_amount_or_streak(self) -> None:
        _spend(self.groceries, "10", date(2026, 10, 2))
        snap = build_month_snapshot(self.budget, today=date(2026, 11, 3))
        self.assertFalse(snap.is_current)
        self.assertIsNone(snap.safe_today)
        self.assertEqual(snap.streak, 0)

    def test_streak_counts_days_under_limit_back_from_today(self) -> None:
        # Daily limit: 3100 / 31 = 100.
        _spend(self.groceries, "90", date(2026, 10, 8))
        _spend(self.groceries, "150", date(2026, 10, 9))  # Over: the streak stops here.
        _spend(self.groceries, "40", date(2026, 10, 10))
        _spend(self.groceries, "100", date(2026, 10, 12))
        snap = build_month_snapshot(self.budget, today=date(2026, 10, 14))
        self.assertEqual(snap.daily_limit, D("100.00"))
        self.assertEqual(snap.streak, 5)  # 10th to 14th
        bars = {bar.day: bar for bar in snap.days}
        self.assertTrue(bars[9].is_over)
        self.assertTrue(bars[14].is_today)
        self.assertTrue(bars[15].is_future)

    def test_streak_starts_at_first_recorded_spend(self) -> None:
        _spend(self.groceries, "20", date(2026, 10, 13))
        snap = build_month_snapshot(self.budget, today=date(2026, 10, 14))
        self.assertEqual(snap.streak, 2)

    def test_accounts_include_transfers(self) -> None:
        TagTransfer.objects.create(
            budget=self.budget, from_tag=self.bank, to_tag=self.cash, amount=D("400")
        )
        _spend(self.groceries, "1000", date(2026, 10, 2))
        snap = build_month_snapshot(self.budget, today=date(2026, 10, 14))
        accounts = {a.name: (a.total, a.used) for a in snap.accounts}
        self.assertEqual(accounts["Cash"], (D("3500"), D("1000")))
        self.assertEqual(accounts["Bank"], (D("4600"), D("0")))

    def test_categories_group_lines(self) -> None:
        snap = build_month_snapshot(self.budget, today=date(2026, 10, 14))
        self.assertEqual(
            [(g.name, g.amount) for g in snap.categories],
            [("Uncategorized", D("5000")), ("Food", D("3100"))],
        )


class QuickAddParseTests(TestCase):
    """parse_amount and parse_spend_text."""

    def test_amount_formats(self) -> None:
        self.assertEqual(parse_amount("2500"), D("2500.00"))
        self.assertEqual(parse_amount("2,500"), D("2500.00"))
        self.assertEqual(parse_amount("12.5"), D("12.50"))
        self.assertEqual(parse_amount("2.5k"), D("2500.00"))
        self.assertEqual(parse_amount("3K"), D("3000.00"))

    def test_bad_amounts(self) -> None:
        for raw in ("", "abc", "0", "-5", "1.234", "999999999"):
            with self.subTest(raw=raw), self.assertRaises(QuickAddError):
                parse_amount(raw)

    def test_text_in_any_order(self) -> None:
        parsed = parse_spend_text("#Cash 2500 eating out")
        self.assertEqual(parsed.amount, D("2500.00"))
        self.assertEqual(parsed.words, "eating out")
        self.assertEqual(parsed.account, "cash")

    def test_spent_at_from_offline_saves(self) -> None:
        now = timezone.make_aware(datetime(2026, 10, 14, 12, 0))
        two_hours_ago = int((now.timestamp() - 7200) * 1000)
        self.assertEqual(
            parse_spent_at(str(two_hours_ago), now).timestamp(), now.timestamp() - 7200
        )
        for raw in ("", "abc", str(int(now.timestamp() * 1000) + 3_600_000), "1000", "9" * 30):
            with self.subTest(raw=raw):
                self.assertIsNone(parse_spent_at(raw, now))

    def test_text_needs_exactly_one_amount(self) -> None:
        with self.assertRaises(QuickAddError):
            parse_spend_text("groceries")
        with self.assertRaises(QuickAddError):
            parse_spend_text("groceries 20 30")


class MatchLinesTests(TestCase):
    """match_lines picks lines by name, category and account."""

    def setUp(self) -> None:
        user = User.objects.create_user(
            username="match", email="match@example.com", password="testpassword"
        )
        cash = Tag.objects.create(user=user, name="Cash", slug="cash")
        bank = Tag.objects.create(user=user, name="Bank", slug="bank")
        travel = Category.objects.create(user=user, name="Travel", slug="travel")
        self.budget = Budget.objects.create(user=user, month=date(2026, 10, 1))
        self.groceries = Expense.objects.create(
            budget=self.budget, name="Groceries", amount=D("1"), tag_foreign_key=cash
        )
        self.gifts = Expense.objects.create(
            budget=self.budget, name="Gifts", amount=D("1"), tag_foreign_key=cash
        )
        self.fuel = Expense.objects.create(
            budget=self.budget, name="Fuel", amount=D("1"), category=travel, tag_foreign_key=bank
        )

    def test_rules(self) -> None:
        self.assertEqual(match_lines(self.budget, "groceries"), [self.groceries])
        self.assertEqual(match_lines(self.budget, "gro"), [self.groceries])
        self.assertEqual(match_lines(self.budget, "cer"), [self.groceries])
        self.assertEqual(match_lines(self.budget, "travel"), [self.fuel])
        self.assertEqual(match_lines(self.budget, "g"), [self.gifts, self.groceries])
        self.assertEqual(match_lines(self.budget, "rent"), [])

    def test_account_narrows_the_match(self) -> None:
        self.assertEqual(match_lines(self.budget, "", "ba"), [self.fuel])
        self.assertEqual(match_lines(self.budget, "g", "bank"), [])
        self.assertEqual(match_lines(self.budget, "", "cash"), [])  # 2 lines: ask the user


class CreateMonthTests(TestCase):
    """create_month copies income and recurring lines from the latest earlier month."""

    def setUp(self) -> None:
        self.user = User.objects.create_user(
            username="months", email="months@example.com", password="testpassword"
        )
        sept = Budget.objects.create(
            user=self.user, month=date(2026, 9, 1), income=D("900"), currency="USD"
        )
        Expense.objects.create(
            budget=sept, name="Rent", amount=D("500"), is_recurring=True, is_daily=False
        )
        Expense.objects.create(
            budget=sept, name="Food", amount=D("200"), is_recurring=True, is_daily=True
        )
        Expense.objects.create(budget=sept, name="Trip", amount=D("100"))

    def test_copies_income_currency_and_recurring_lines(self) -> None:
        created = create_month(self.user, date(2026, 10, 14))
        budget = created.budget
        self.assertEqual(budget.month, date(2026, 10, 1))
        self.assertEqual((budget.income, budget.currency), (D("900"), "USD"))
        self.assertEqual(created.copied_lines, 2)
        lines = {e.name: e.is_daily for e in budget.expenses.all()}
        self.assertEqual(lines, {"Rent": False, "Food": True})

    def test_empty_month(self) -> None:
        created = create_month(self.user, date(2026, 10, 1), copy_previous=False)
        self.assertIsNone(created.copied_from)
        self.assertEqual(created.budget.expenses.count(), 0)
        self.assertEqual(created.budget.income, D("0"))


class BillsTests(TestCase):
    """month_bills and coming_up: applied bills, pending reminders and states."""

    def setUp(self) -> None:
        self.user = User.objects.create_user(
            username="bills", email="bills@example.com", password="testpassword"
        )
        self.budget = Budget.objects.create(user=self.user, month=date(2026, 10, 1))
        self.today = date(2026, 10, 14)

    def _reminder(self, name: str, due: date, amount: str = "1000") -> BillReminder:
        return BillReminder.objects.create(
            user=self.user, name=name, amount=D(amount), next_bill_date=due, recurrence_months=12
        )

    def _bills(self) -> list:
        return month_bills(self.budget, build_month_snapshot(self.budget, self.today), self.today)

    def test_applied_and_pending_bills(self) -> None:
        self._reminder("Car tax", date(2026, 10, 10))
        self._reminder("Insurance", date(2026, 10, 20))
        apply_bill_reminders_to_budget(self.budget)
        self._reminder("Domain", date(2026, 10, 16))  # Added after the month was made.
        self._reminder("Next year", date(2026, 11, 2))
        bills = self._bills()
        self.assertEqual(
            [(b.name, b.due, b.state) for b in bills],
            [
                ("Car tax", date(2026, 10, 10), "late"),
                ("Domain", date(2026, 10, 16), "unplanned"),
                ("Insurance", date(2026, 10, 20), "soon"),
            ],
        )
        self.assertIsNone(bills[1].line_id)

    def test_paid_bill(self) -> None:
        self._reminder("Car tax", date(2026, 10, 10))
        apply_bill_reminders_to_budget(self.budget)
        line = self.budget.expenses.get()
        SubExpense.objects.create(expense=line, name="paid", amount=D("1000"))
        bill = self._bills()[0]
        self.assertEqual((bill.is_paid, bill.state), (True, "paid"))
        snap = build_month_snapshot(self.budget, self.today)
        self.assertEqual(coming_up(self.budget, snap, self.today), [])

    def test_coming_up_adds_later_months(self) -> None:
        self._reminder("Insurance", date(2026, 10, 20))
        apply_bill_reminders_to_budget(self.budget)
        self._reminder("Car tax", date(2027, 1, 5))
        self._reminder("Domain", date(2026, 11, 1))
        snap = build_month_snapshot(self.budget, self.today)
        names = [b.name for b in coming_up(self.budget, snap, self.today)]
        self.assertEqual(names, ["Insurance", "Domain", "Car tax"])
        self.assertEqual(len(coming_up(self.budget, snap, self.today, limit=2)), 2)


class RecapTests(TestCase):
    """month_recap and last_month_recap."""

    def setUp(self) -> None:
        self.user = User.objects.create_user(
            username="recap", email="recap@example.com", password="testpassword"
        )
        food = Category.objects.create(user=self.user, name="Food", slug="food")
        self.budget = Budget.objects.create(
            user=self.user, month=date(2026, 9, 1), income=D("10000")
        )
        # 30 days, daily limit 3000 / 30 = 100.
        self.groceries = Expense.objects.create(
            budget=self.budget, name="Groceries", amount=D("3000"), is_daily=True, category=food
        )
        self.fun = Expense.objects.create(budget=self.budget, name="Fun", amount=D("100"))

    def test_recap_figures(self) -> None:
        _spend(self.groceries, "500", date(2026, 9, 10))  # Over the limit.
        _spend(self.groceries, "100", date(2026, 9, 11), is_return=True)
        _spend(self.fun, "300", date(2026, 9, 12))
        goal = Goal.objects.create(user=self.user, name="Trip", target_amount=D("1"))
        GoalContribution.objects.create(goal=goal, amount=D("700"), date=date(2026, 9, 20))
        GoalContribution.objects.create(goal=goal, amount=D("50"), date=date(2026, 10, 1))
        recap = month_recap(self.budget, date(2026, 10, 2))
        self.assertEqual((recap.net_spent, recap.kept), (D("700"), D("9300")))
        self.assertEqual((recap.top_category, recap.top_category_spent), ("Food", D("500")))
        self.assertEqual((recap.days_under, recap.days_counted, recap.best_run), (29, 30, 20))
        self.assertEqual([line.name for line in recap.over_lines], ["Fun"])
        self.assertEqual(recap.to_goals, D("700"))

    def test_home_shows_last_month_only_in_the_first_week(self) -> None:
        self.assertIsNotNone(last_month_recap(self.user, date(2026, 10, 7)))
        self.assertIsNone(last_month_recap(self.user, date(2026, 10, 8)))
        self.assertIsNone(last_month_recap(self.user, date(2026, 12, 3)))  # No November.
