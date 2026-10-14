"""Tests for goals and debts in the new UI: the service rules and the views."""

from __future__ import annotations

import json
from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from budgetapp.models import Budget, Debt, DebtTransaction, Expense, Goal, GoalContribution
from budgetapp.services.goals import add_repayment, debt_view, goal_views, milestone_passed

User = get_user_model()
D = Decimal


class GoalServiceTests(TestCase):
    """Milestones, goal order and the sum of contributions."""

    def setUp(self) -> None:
        self.user = User.objects.create_user(
            username="goals", email="goals@example.com", password="testpassword"
        )

    def test_milestone_passed(self) -> None:
        self.assertEqual(milestone_passed(10, 30), 25)
        self.assertEqual(milestone_passed(20, 80), 75)
        self.assertEqual(milestone_passed(25, 49), None)
        self.assertEqual(milestone_passed(99, 100), 100)
        self.assertEqual(milestone_passed(100, 100), None)

    def test_goal_views_order_and_amount(self) -> None:
        trip = Goal.objects.create(user=self.user, name="Trip", target_amount=D("1000"))
        phone = Goal.objects.create(user=self.user, name="Phone", target_amount=D("100"))
        done = Goal.objects.create(user=self.user, name="Fund", target_amount=D("10"))
        GoalContribution.objects.create(goal=trip, amount=D("600"))
        GoalContribution.objects.create(goal=phone, amount=D("20"))
        GoalContribution.objects.create(goal=done, amount=D("10"))
        Goal.objects.create(user=self.user, name="Old", target_amount=D("5"), is_active=False)
        views = goal_views(self.user)
        self.assertEqual([v.name for v in views], ["Trip", "Phone", "Fund"])
        self.assertEqual((views[0].current, views[0].left, views[0].pct), (D("600"), D("400"), 60))
        self.assertTrue(views[2].is_done)


class DebtServiceTests(TestCase):
    """Owed amount, payoff month and repayments."""

    def setUp(self) -> None:
        self.user = User.objects.create_user(
            username="debts", email="debts@example.com", password="testpassword"
        )
        self.debt = Debt.objects.create(user=self.user, name="Laptop", total_amount=D("30000"))
        DebtTransaction.objects.create(debt=self.debt, amount=D("12000"))
        self.debt.refresh_from_db()

    def _repay(self, month: date, amount: str) -> None:
        budget, _ = Budget.objects.get_or_create(user=self.user, month=month)
        Expense.objects.create(
            budget=budget, name="Repay", amount=D(amount), tag_foreign_key=self.debt.debt_tag
        )

    def test_no_repayment_has_no_payoff_month(self) -> None:
        view = debt_view(self.debt, date(2026, 10, 14))
        self.assertEqual((view.borrowed, view.owed, view.repaid_pct), (D("12000"), D("12000"), 0))
        self.assertIsNone(view.payoff_month)
        self.assertEqual(view.can_borrow, D("18000"))

    def test_payoff_month_uses_average_since_first_repayment(self) -> None:
        # 3,000 in August, nothing in September, 3,000 in October: 2,000 a month.
        self._repay(date(2026, 8, 1), "3000")
        self._repay(date(2026, 10, 1), "3000")
        view = debt_view(self.debt, date(2026, 10, 14))
        self.assertEqual((view.repaid, view.owed), (D("6000"), D("6000")))
        self.assertEqual(view.monthly_repayment, D("2000.00"))
        self.assertEqual(view.payoff_month, date(2027, 1, 1))  # 3 months after October
        self.assertEqual(view.repaid_pct, 50)

    def test_add_repayment_grows_one_line_and_closes_the_debt(self) -> None:
        budget = Budget.objects.create(user=self.user, month=date(2026, 10, 1))
        add_repayment(self.debt, budget, D("2000"))
        line = add_repayment(self.debt, budget, D("10000"))
        self.assertEqual(budget.expenses.count(), 1)
        self.assertEqual((line.name, line.amount), ("Repay Laptop", D("12000")))
        view = debt_view(self.debt, date(2026, 10, 14))
        self.assertTrue(view.is_paid_off)
        self.debt.debt_tag.refresh_from_db()
        self.assertFalse(self.debt.debt_tag.is_active)


class GoalsViewTests(TestCase):
    """The goals page and its forms."""

    def setUp(self) -> None:
        self.user = User.objects.create_user(
            username="gview", email="gview@example.com", password="testpassword"
        )
        self.client = Client()
        self.client.force_login(self.user)
        self.goal = Goal.objects.create(user=self.user, name="Trip", target_amount=D("1000"))
        self.debt = Debt.objects.create(user=self.user, name="Laptop", total_amount=D("5000"))
        DebtTransaction.objects.create(debt=self.debt, amount=D("3000"))
        self.today = timezone.localdate()

    def test_page_and_panel(self) -> None:
        response = self.client.get(reverse("app:goals"))
        self.assertContains(response, "Trip")
        self.assertContains(response, "Laptop")
        self.assertContains(response, "Add a repayment to see when it ends.")
        self.assertContains(self.client.get(reverse("app:goals_panel")), 'id="goals-panel"')
        self.assertEqual(Client().get(reverse("app:goals")).status_code, 302)

    def test_create_goal_with_starting_amount(self) -> None:
        response = self.client.post(
            reverse("app:goal_create"),
            {"goal-name": "Phone", "goal-target_amount": "800", "goal-saved": "200"},
        )
        self.assertContains(response, 'Started the goal "Phone"')
        self.assertEqual(response["HX-Trigger"], "goalsChanged")
        goal = Goal.objects.get(name="Phone")
        self.assertEqual((goal.user, goal.current_amount), (self.user, D("200")))
        # The starting amount is a contribution, so the classic pages keep it.
        self.client.get(reverse("minimal:goal_list"))
        goal.refresh_from_db()
        self.assertEqual(goal.current_amount, D("200"))

    def test_goal_form_errors(self) -> None:
        response = self.client.post(
            reverse("app:goal_create"),
            {
                "goal-name": "Bad",
                "goal-target_amount": "100",
                "goal-saved": "500",
                "goal-target_date": "2000-01-01",
            },
        )
        self.assertContains(response, "cannot be more than the target")
        self.assertContains(response, "Pick a date in the future.")
        self.assertNotIn("HX-Trigger", response)
        self.assertFalse(Goal.objects.filter(name="Bad").exists())

    def test_contribute_and_milestone(self) -> None:
        url = reverse("app:goal_contribute", kwargs={"pk": self.goal.pk})
        response = self.client.post(url, {"amount": "100"})
        self.assertContains(response, "Added 100 to Trip.")
        self.assertEqual(json.loads(response["HX-Trigger"]), {"goalsChanged": True})
        response = self.client.post(url, {"amount": "200"})  # 30 %: passes 25 %
        self.assertContains(response, "25%!")
        self.assertEqual(
            json.loads(response["HX-Trigger"]), {"goalsChanged": True, "celebrate": True}
        )
        response = self.client.post(url, {"amount": "700"})
        self.assertContains(response, "Goal reached!")
        self.goal.refresh_from_db()
        self.assertEqual(self.goal.current_amount, D("1000"))

    def test_contribute_error(self) -> None:
        url = reverse("app:goal_contribute", kwargs={"pk": self.goal.pk})
        response = self.client.post(url, {"amount": "zero"})
        self.assertContains(response, "toast--error")
        self.assertNotIn("HX-Trigger", response)
        self.assertFalse(GoalContribution.objects.exists())

    def test_create_debt(self) -> None:
        response = self.client.post(
            reverse("app:debt_create"),
            {"debt-name": "Bike", "debt-total_amount": "9000", "debt-borrowed": "4000"},
        )
        self.assertContains(response, 'Added the debt "Bike"')
        debt = Debt.objects.get(name="Bike")
        self.assertEqual((debt.user, debt.borrowed_amount), (self.user, D("4000")))
        self.assertIsNotNone(debt.debt_tag)
        response = self.client.post(
            reverse("app:debt_create"),
            {"debt-name": "Too much", "debt-total_amount": "10", "debt-borrowed": "20"},
        )
        self.assertContains(response, "more than the most you may borrow")

    def test_repay_needs_this_month(self) -> None:
        url = reverse("app:debt_repay", kwargs={"pk": self.debt.pk})
        response = self.client.post(url, {"amount": "1000"})
        self.assertContains(response, "Start this month")
        Budget.objects.create(user=self.user, month=self.today.replace(day=1))
        response = self.client.post(url, {"amount": "1000"})
        self.assertContains(response, "Added 1,000 to the line Repay Laptop")
        response = self.client.post(url, {"amount": "2000"})
        self.assertContains(response, "Debt free!")
        self.assertIn("celebrate", json.loads(response["HX-Trigger"]))

    def test_borrow_up_to_the_limit(self) -> None:
        url = reverse("app:debt_borrow", kwargs={"pk": self.debt.pk})
        response = self.client.post(url, {"amount": "3000"})
        self.assertContains(response, "You can borrow 2,000 more at most.")
        response = self.client.post(url, {"amount": "2000"})
        self.assertContains(response, "Recorded 2,000 borrowed")
        self.debt.refresh_from_db()
        self.assertEqual(self.debt.borrowed_amount, D("5000"))

    def test_other_users_goal_and_debt_are_404(self) -> None:
        other = User.objects.create_user(
            username="other", email="other@example.com", password="testpassword"
        )
        goal = Goal.objects.create(user=other, name="Theirs", target_amount=D("10"))
        debt = Debt.objects.create(user=other, name="Theirs", total_amount=D("10"))
        urls = [
            reverse("app:goal_contribute", kwargs={"pk": goal.pk}),
            reverse("app:debt_repay", kwargs={"pk": debt.pk}),
            reverse("app:debt_borrow", kwargs={"pk": debt.pk}),
        ]
        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(self.client.post(url, {"amount": "5"}).status_code, 404)
        self.assertFalse(GoalContribution.objects.exists())
        self.assertNotContains(self.client.get(reverse("app:goals")), "Theirs")
