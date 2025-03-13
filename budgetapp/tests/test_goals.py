from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from budgetapp.models import Category, Goal, GoalContribution

User = get_user_model()


class GoalModelTests(TestCase):
    def setUp(self):
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

    def test_goal_creation(self):
        """Test that a goal can be created with the correct fields"""
        self.assertEqual(self.goal.name, "Vacation Fund")
        self.assertEqual(self.goal.target_amount, Decimal("1000.00"))
        self.assertEqual(self.goal.current_amount, Decimal("250.00"))
        self.assertEqual(self.goal.user, self.user)
        self.assertEqual(self.goal.category, self.category)
        self.assertTrue(self.goal.is_active)

    def test_progress_percentage(self):
        """Test that progress_percentage returns the correct value"""
        # 250 / 1000 = 25%
        self.assertEqual(self.goal.progress_percentage, 25)

        # Update current amount and check again
        self.goal.current_amount = Decimal("500.00")
        self.goal.save()
        self.assertEqual(self.goal.progress_percentage, 50)

        # Edge case: target amount is 0
        goal_zero_target = Goal.objects.create(
            user=self.user,
            name="Test Zero Target",
            target_amount=Decimal("0.00"),
            current_amount=Decimal("0.00"),
        )
        self.assertEqual(goal_zero_target.progress_percentage, 100)

    def test_is_on_track(self):
        """Test the is_on_track method"""
        # Create a contribution to test being on track
        GoalContribution.objects.create(
            goal=self.goal,
            amount=Decimal("250.00"),
            date=timezone.now().date() - timedelta(days=15),
            source="Savings",
        )

        # With this contribution rate and 75 days remaining, should be on track
        self.assertTrue(self.goal.is_on_track())

        # Change target date to make it behind schedule
        original_current_amount = self.goal.current_amount
        self.goal.target_date = timezone.now().date() + timedelta(days=10)
        # Reduce current amount to be far from target
        self.goal.current_amount = Decimal("300.00")
        self.goal.target_amount = Decimal("1000.00")
        self.goal.save()

        # Debug output
        print(f"Current amount: {self.goal.current_amount}")
        print(f"Target amount: {self.goal.target_amount}")
        print(f"Days remaining: {(self.goal.target_date - timezone.now().date()).days}")
        print(f"Total days: {(self.goal.target_date - self.goal.start_date).days}")
        print(f"Days passed: {(timezone.now().date() - self.goal.start_date).days}")
        print(f"Is on track: {self.goal.is_on_track()}")

        # Force a very behind schedule scenario by requiring almost all money in very little time
        self.goal.current_amount = Decimal("10.00")
        self.goal.target_amount = Decimal("1000.00")
        self.goal.target_date = timezone.now().date() + timedelta(days=2)
        self.goal.save()

        # Debug output
        print(f"After update - Current amount: {self.goal.current_amount}")
        print(f"After update - Target amount: {self.goal.target_amount}")
        print(
            f"After update - Days remaining: {(self.goal.target_date - timezone.now().date()).days}"
        )
        print(f"After update - Is on track: {self.goal.is_on_track()}")

        # Should now be behind schedule (need to save too much in too little time)
        self.assertFalse(self.goal.is_on_track())

        # Restore original amount
        self.goal.current_amount = original_current_amount

        # Remove target date
        self.goal.target_date = None
        self.goal.save()

        # Without a target date, is_on_track should return None
        self.assertIsNone(self.goal.is_on_track())


class GoalViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpassword"
        )
        self.client.login(username="testuser", password="testpassword")

        self.goal = Goal.objects.create(
            user=self.user,
            name="Test Goal",
            target_amount=Decimal("1000.00"),
            current_amount=Decimal("0.00"),
            start_date=timezone.now().date(),
            target_date=timezone.now().date() + timedelta(days=60),
            is_active=True,
        )

    def test_goal_list_view(self):
        """Test the goal list view shows goals"""
        # Create another goal that's completed
        Goal.objects.create(
            user=self.user,
            name="Completed Goal",
            target_amount=Decimal("1000.00"),
            current_amount=Decimal("1000.00"),
            is_active=True,
        )

        # Create an inactive goal
        Goal.objects.create(
            user=self.user,
            name="Inactive Goal",
            target_amount=Decimal("1000.00"),
            current_amount=Decimal("250.00"),
            is_active=False,
        )

        response = self.client.get(reverse("goal_list"))
        self.assertEqual(response.status_code, 200)

        # Check that the goals appear in their respective sections
        self.assertContains(response, "Test Goal")
        self.assertContains(response, "Completed Goal")
        self.assertContains(response, "Inactive Goal")

    def test_goal_detail_view(self):
        """Test the goal detail view shows goal details"""
        # Add a contribution to the goal
        GoalContribution.objects.create(
            goal=self.goal, amount=Decimal("250.00"), date=timezone.now().date(), source="Savings"
        )

        response = self.client.get(reverse("goal_detail", kwargs={"goal_id": self.goal.id}))
        self.assertEqual(response.status_code, 200)

        # Check that the goal details are displayed
        self.assertContains(response, self.goal.name)
        self.assertContains(response, "250.00")  # The contribution amount
        self.assertContains(response, "Savings")  # The contribution source

    def test_add_contribution(self):
        """Test adding a contribution to a goal"""
        self.assertEqual(self.goal.current_amount, Decimal("0.00"))

        # Post a new contribution
        response = self.client.post(
            reverse("add_contribution", kwargs={"goal_id": self.goal.id}),
            {
                "amount": "100.00",
                "date": timezone.now().date().isoformat(),
                "source": "Test",
                "notes": "Test contribution",
            },
        )

        # Should redirect back to goal detail
        self.assertEqual(response.status_code, 302)

        # Check that the goal's current_amount was updated
        self.goal.refresh_from_db()
        self.assertEqual(self.goal.current_amount, Decimal("100.00"))

        # Check that the contribution was created
        self.assertTrue(
            GoalContribution.objects.filter(goal=self.goal, amount=Decimal("100.00")).exists()
        )
