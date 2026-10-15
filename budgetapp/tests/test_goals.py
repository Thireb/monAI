"""Tests for the savings goal model (the views are in test_app_goals)."""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from budgetapp.models import Category, Goal, GoalContribution

User = get_user_model()


class GoalModelTests(TestCase):
    """Tests for Goal model properties and progress helpers."""

    def setUp(self) -> None:
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpassword"
        )
        self.category = Category.objects.create(name="Savings", slug="savings", color="#28a745")
        self.goal = Goal.objects.create(
            user=self.user,
            name="Vacation Fund",
            description="Saving for summer vacation",
            target_amount=Decimal("1000.00"),
            current_amount=Decimal("250.00"),
            start_date=timezone.now().date(),
            target_date=timezone.now().date() + timedelta(days=90),
            category=self.category,
            is_active=True,
        )

    def test_goal_creation(self) -> None:
        """Test that a goal can be created with the correct fields"""
        self.assertEqual(self.goal.name, "Vacation Fund")
        self.assertEqual(self.goal.target_amount, Decimal("1000.00"))
        self.assertEqual(self.goal.current_amount, Decimal("250.00"))
        self.assertEqual(self.goal.user, self.user)
        self.assertEqual(self.goal.category, self.category)
        self.assertTrue(self.goal.is_active)

    def test_progress_percentage(self) -> None:
        """Test that progress_percentage returns the correct value"""
        self.assertEqual(self.goal.progress_percentage, 25)

        self.goal.current_amount = Decimal("500.00")
        self.goal.save()
        self.assertEqual(self.goal.progress_percentage, 50)

        goal_zero_target = Goal.objects.create(
            user=self.user,
            name="Test Zero Target",
            target_amount=Decimal("0.00"),
            current_amount=Decimal("0.00"),
        )
        self.assertEqual(goal_zero_target.progress_percentage, 100)

    def test_is_on_track(self) -> None:
        """Test the is_on_track method"""
        GoalContribution.objects.create(
            goal=self.goal,
            amount=Decimal("250.00"),
            date=timezone.now().date() - timedelta(days=15),
            source="Savings",
        )

        self.assertTrue(self.goal.is_on_track())

        self.goal.target_date = timezone.now().date() + timedelta(days=10)
        self.goal.current_amount = Decimal("300.00")
        self.goal.target_amount = Decimal("1000.00")
        self.goal.save()

        self.goal.current_amount = Decimal("10.00")
        self.goal.target_amount = Decimal("1000.00")
        self.goal.target_date = timezone.now().date() + timedelta(days=2)
        self.goal.save()

        self.assertFalse(self.goal.is_on_track())

        self.goal.target_date = None
        self.goal.save()

        self.assertIsNone(self.goal.is_on_track())
