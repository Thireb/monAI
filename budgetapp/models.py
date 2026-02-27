from decimal import Decimal

from django.conf import settings
from django.db import models
from django.db.models import DecimalField, Sum, Value
from django.db.models.functions import Coalesce
from django.utils import timezone
from django.utils.text import slugify


class Budget(models.Model):
    """
    Represents a monthly budget with income and expenses.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="budgets",
        null=True,
        blank=True,
    )
    month = models.DateField()
    income = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0"))
    currency = models.CharField(max_length=3, default="PKR")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_archived = models.BooleanField(default=False)

    class Meta:
        ordering = ["-month"]
        verbose_name_plural = "Budgets"
        indexes = [
            models.Index(fields=["-month"]),
        ]

    def __str__(self):
        return self.month.strftime("%B %Y")

    def was_edited(self):
        """Return True if the budget was edited after creation"""
        return self.updated_at > self.created_at

    def get_remaining_budget(self):
        """Calculate remaining budget after all expenses, accounting for returns"""
        # Get all expenses
        expenses = self.expenses.all()

        # Calculate total expense amounts
        total_expenses = expenses.aggregate(
            total=Coalesce(Sum("amount"), Value(0), output_field=DecimalField())
        )["total"]

        # Calculate total returns from all sub-expenses
        total_returns = Decimal("0")
        for expense in expenses:
            total_returns += expense.get_total_returns()

        # Remaining is: income - expenses + returns
        return self.income - total_expenses + total_returns

    def get_total_returns(self):
        """Calculate total returns from all expenses"""
        total_returns = Decimal("0")
        for expense in self.expenses.all():
            total_returns += expense.get_total_returns()
        return total_returns

    @staticmethod
    def get_currency_choices():
        # Common currencies with their names
        currencies = [
            ("PKR", "PKR - Pakistani Rupee"),
            ("USD", "USD - US Dollar"),
            ("EUR", "EUR - Euro"),
            ("GBP", "GBP - British Pound"),
            ("AUD", "AUD - Australian Dollar"),
            ("CAD", "CAD - Canadian Dollar"),
            ("JPY", "JPY - Japanese Yen"),
            ("CNY", "CNY - Chinese Yuan"),
            ("INR", "INR - Indian Rupee"),
            ("AED", "AED - UAE Dirham"),
            ("SAR", "SAR - Saudi Riyal"),
        ]
        return currencies


class Category(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="categories",
        null=True,
        blank=True,
    )
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True, help_text="Font Awesome icon class")
    color = models.CharField(max_length=7, default="#000000", help_text="Hex color code")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "name"],
                name="unique_category_name_per_user",
            ),
            models.UniqueConstraint(
                fields=["user", "slug"],
                name="unique_category_slug_per_user",
            ),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Tag(models.Model):
    """Custom tags for expenses that can be created by users."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="tags",
        null=True,
        blank=True,
    )
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100)
    description = models.TextField(blank=True)
    color = models.CharField(max_length=7, default="#2196f3", help_text="Hex color code")
    is_active = models.BooleanField(
        default=True, help_text="Whether this tag is active for new expenses"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Tags"
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "name"],
                name="unique_tag_name_per_user",
            ),
            models.UniqueConstraint(
                fields=["user", "slug"],
                name="unique_tag_slug_per_user",
            ),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Expense(models.Model):
    budget = models.ForeignKey(Budget, on_delete=models.CASCADE, related_name="expenses")
    name = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    is_recurring = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="expenses",
    )
    # Tag for this expense (replaces the old CharField-based tag)
    tag_foreign_key = models.ForeignKey(
        Tag,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="expenses",
        help_text="Custom tag for this expense",
    )

    def __str__(self):
        return f"{self.name} - {self.amount}"

    def get_remaining_amount(self):
        # Get all sub expenses
        sub_expenses = self.sub_expenses.all()

        # Calculate total spent (all sub-expenses, including returns)
        total_spent = sub_expenses.aggregate(total=models.Sum("amount"))["total"] or Decimal("0")

        # Remaining is simply: original amount - all spent (including returns)
        # Returns don't increase the remaining amount of the expense itself
        return self.amount - total_spent

    def get_total_returns(self):
        # Calculate total returns (sub-expenses marked as returns)
        total_returns = self.sub_expenses.filter(is_return=True).aggregate(
            total=models.Sum("amount")
        )["total"] or Decimal("0")
        return total_returns

    def get_net_amount(self):
        """Return the net amount (amount minus returns) for this expense."""
        return self.amount - self.get_remaining_amount()

    @property
    def subexpense_total(self):
        # Sum of all sub-expenses (excluding returns)
        return (
            self.sub_expenses.filter(is_return=False).aggregate(total=models.Sum("amount"))["total"]
            or 0
        )


class SubExpense(models.Model):
    expense = models.ForeignKey(Expense, on_delete=models.CASCADE, related_name="sub_expenses")
    name = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    is_return = models.BooleanField(
        default=False,
        help_text="Mark as return/refund to add this amount back to the remaining budget",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        prefix = "Return: " if self.is_return else ""
        return f"{prefix}{self.name} - {self.amount}"


class BudgetLog(models.Model):
    ACTIONS = (
        ("create", "Created"),
        ("update", "Updated"),
        ("delete", "Deleted"),
    )

    month = models.DateField()
    action = models.CharField(max_length=10, choices=ACTIONS)
    timestamp = models.DateTimeField(auto_now_add=True)
    details = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.get_action_display()} - {self.month.strftime('%B %Y')}"


class ArchivedBudget(models.Model):
    budget = models.OneToOneField("Budget", on_delete=models.CASCADE)
    archived_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-budget__month"]

    def __str__(self):
        return f"Archive: {self.budget.month.strftime('%Y-%m')}"


class BudgetDeletionLog(models.Model):
    month = models.DateField()
    deleted_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    class Meta:
        ordering = ["-deleted_at"]

    def __str__(self):
        return (
            f"Budget for {self.month.strftime('%B %Y')} "
            f"deleted on {self.deleted_at.strftime('%Y-%m-%d %H:%M')}"
        )


class IncomeHistory(models.Model):
    budget = models.ForeignKey(Budget, on_delete=models.CASCADE, related_name="income_history")
    old_amount = models.DecimalField(max_digits=10, decimal_places=2)
    new_amount = models.DecimalField(max_digits=10, decimal_places=2)
    old_currency = models.CharField(max_length=3)
    new_currency = models.CharField(max_length=3)
    changed_at = models.DateTimeField(auto_now_add=True)
    reason = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["-changed_at"]
        verbose_name_plural = "Income histories"

    def __str__(self):
        return f"Income change for {self.budget.month.strftime('%B %Y')}"


class RecentUpdate(models.Model):
    budget = models.ForeignKey("Budget", on_delete=models.CASCADE, related_name="recent_updates")
    action_type = models.CharField(max_length=50)  # e.g., 'expense_added', 'income_updated'
    description = models.TextField()
    timestamp = models.DateTimeField(default=timezone.now)
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    category = models.ForeignKey("Category", on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.action_type} - {self.description}"


class Goal(models.Model):
    """Financial goal that a user is saving towards."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True
    )
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    target_amount = models.DecimalField(max_digits=10, decimal_places=2)
    current_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    start_date = models.DateField(default=timezone.now)
    target_date = models.DateField(null=True, blank=True)
    category = models.ForeignKey("Category", on_delete=models.SET_NULL, null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    @property
    def progress_percentage(self):
        """Return the percentage of progress towards the goal."""
        if self.target_amount == 0:
            return 100
        return min(100, int((self.current_amount / self.target_amount) * 100))

    def get_average_contribution(self):
        """
        Calculate the average contribution amount based on contribution history.
        Returns tuple of (amount, frequency_in_days)
        """
        contributions = self.contributions.all().order_by("date")
        if not contributions:
            return Decimal("0"), None

        # Get all contribution amounts
        amounts = [c.amount for c in contributions]

        # Calculate average amount
        avg_amount = sum(amounts) / len(amounts)

        # Calculate average frequency in days
        if len(contributions) > 1:
            # Get all dates
            dates = [c.date for c in contributions]
            # Calculate differences between consecutive dates
            intervals = [(dates[i + 1] - dates[i]).days for i in range(len(dates) - 1)]
            # Calculate average interval
            avg_frequency = sum(intervals) / len(intervals)
        else:
            # If only one contribution, use days since that contribution
            first_contrib_date = contributions[0].date
            days_since = (timezone.now().date() - first_contrib_date).days
            avg_frequency = max(days_since, 30)  # Use at least 30 days if very recent

        return avg_amount, avg_frequency

    def get_projected_completion(self):
        """
        Calculate projected completion date and final amount based on contribution patterns.
        Returns tuple of (projected_date, monthly_rate, is_on_target)
        """
        if self.current_amount >= self.target_amount:
            return None, Decimal("0"), True

        avg_amount, avg_frequency = self.get_average_contribution()

        if not avg_amount or not avg_frequency:
            return None, Decimal("0"), False

        # Calculate remaining amount needed
        remaining = self.target_amount - self.current_amount

        # Convert to monthly rate for comparison
        monthly_rate = (avg_amount * 30) / avg_frequency

        # Calculate number of days needed at current rate
        days_needed = (remaining / avg_amount) * avg_frequency

        # Calculate projected completion date
        projected_date = timezone.now().date() + timezone.timedelta(days=int(days_needed))

        # Determine if we're on target (if target date exists)
        is_on_target = True
        if self.target_date:
            is_on_target = projected_date <= self.target_date

        return projected_date, monthly_rate, is_on_target

    def is_on_track(self):
        """
        Determine if the goal is on track to be completed by the target date.
        Returns True if on track, False if behind, None if no target date.
        """
        if not self.target_date:
            return None

        # If already completed
        if self.current_amount >= self.target_amount:
            return True

        # Calculate how much should be saved by now
        total_days = (self.target_date - self.start_date).days
        if total_days <= 0:
            return False

        days_passed = (timezone.now().date() - self.start_date).days
        days_passed = max(0, min(days_passed, total_days))  # Clamp between 0 and total_days

        # Calculate how much remains to be saved and how many days are left
        remaining_amount = self.target_amount - self.current_amount
        days_remaining = (self.target_date - timezone.now().date()).days

        # If no days remaining but still money to save, definitely behind
        if days_remaining <= 0 and remaining_amount > 0:
            return False

        # Special case for brand new goals with very little time
        if days_passed == 0 and days_remaining <= 5:
            # For extremely short timeframes, check if we're at least 50% there
            if self.current_amount < (self.target_amount * Decimal("0.5")):
                return False

        # If days remaining, calculate daily rate needed
        if days_remaining > 0:
            daily_rate_needed = remaining_amount / Decimal(days_remaining)
            # Get average daily contribution rate so far
            if days_passed > 0:
                daily_rate_so_far = self.current_amount / Decimal(days_passed)
                # Behind if we need to save significantly more per day than we have been
                if daily_rate_needed > daily_rate_so_far * Decimal("1.5"):
                    return False

        # Convert to Decimal to avoid type mixing
        days_ratio = Decimal(days_passed) / Decimal(total_days)
        expected_progress = days_ratio * self.target_amount

        # At least 90% of expected progress is considered on track
        return self.current_amount >= expected_progress * Decimal("0.9")

    def monthly_contribution_needed(self):
        """
        Calculate the monthly contribution needed to reach the goal by the target date.
        Returns None if target date is not set or has passed.
        """
        if not self.target_date:
            return None

        today = timezone.now().date()

        # If target date has passed
        if self.target_date <= today:
            return None

        # Amount still needed
        amount_needed = self.target_amount - self.current_amount
        if amount_needed <= 0:
            return Decimal("0")

        # Calculate months remaining (approximate)
        months_remaining = (
            (self.target_date.year - today.year) * 12 + self.target_date.month - today.month
        )
        if self.target_date.day < today.day:
            months_remaining -= 1  # Adjust if we're past the day of month

        months_remaining = max(1, months_remaining)  # At least 1 month

        # Monthly contribution needed
        return amount_needed / months_remaining


class GoalContribution(models.Model):
    """Contribution towards a financial goal."""

    goal = models.ForeignKey(Goal, on_delete=models.CASCADE, related_name="contributions")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField(default=timezone.now)
    source = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.amount} contribution to {self.goal.name}"


class Debt(models.Model):
    """Represents money borrowed from external sources."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="debts",
        null=True,
        blank=True,
    )
    name = models.CharField(max_length=200)  # e.g., "Motherboard Purchase"
    description = models.TextField(blank=True)  # e.g., "Borrowed from friend for new motherboard"
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)  # e.g., 27,000
    borrowed_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # e.g., 4,000
    debt_tag = models.ForeignKey(
        Tag, on_delete=models.SET_NULL, related_name="debts", null=True, blank=True
    )  # Auto-generated tag
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "Debts"

    def __str__(self):
        return f"{self.name} - {self.borrowed_amount}"

    def save(self, *args, **kwargs):
        # Check if this is a new instance (no pk yet)
        is_new = self.pk is None  # noqa: F841

        # Save first to get the pk
        super().save(*args, **kwargs)

        # Auto-generate tag if not provided and we have a name
        if not self.debt_tag and self.name:
            tag_name = self.generate_debt_tag_name()
            self.debt_tag = Tag.objects.create(
                user=self.user,
                name=tag_name,
                description=f"Tracking tag for debt: {self.name}",
                color="#ff5722",  # Orange-red for debt tags
            )
            # Save again to update the debt_tag field
            super().save(update_fields=["debt_tag"])

    def generate_debt_tag_name(self):
        """Generate unique tag name for debt tracking"""
        base_name = f"Debt: {self.name}"
        counter = 1

        # Filter by user if available
        queryset = Tag.objects.filter(name=base_name)
        if self.user:
            queryset = queryset.filter(user=self.user)

        while queryset.exists():
            base_name = f"Debt: {self.name} ({counter})"
            counter += 1
            queryset = Tag.objects.filter(name=base_name)
            if self.user:
                queryset = queryset.filter(user=self.user)

        return base_name

    @property
    def repaid_amount(self):
        """Calculate total repaid from expenses with this tag"""
        return self.debt_tag.expenses.aggregate(total=models.Sum("amount"))["total"] or Decimal("0")

    @property
    def remaining_to_repay(self):
        return self.borrowed_amount - self.repaid_amount

    @property
    def repayment_progress_percentage(self):
        if self.borrowed_amount == 0:
            return 0
        return min(100, int((self.repaid_amount / self.borrowed_amount) * 100))

    @property
    def progress_percentage(self):
        """Calculate borrowing progress as percentage of total amount"""
        if self.total_amount == 0:
            return 0
        return min(100, int((self.borrowed_amount / self.total_amount) * 100))

    @property
    def is_fully_repaid(self):
        return self.repaid_amount >= self.borrowed_amount

    def check_and_update_status(self):
        """Check if debt is fully repaid and disable tag if so"""
        if self.is_fully_repaid and self.debt_tag.is_active:
            self.debt_tag.is_active = False
            self.debt_tag.save()
            return True
        return False

    def recalculate_borrowed_amount(self):
        """Recalculate borrowed_amount from transactions"""
        total = self.transactions.aggregate(total=models.Sum("amount"))["total"] or Decimal("0")
        if self.borrowed_amount != total:
            self.borrowed_amount = total
            self.save(update_fields=["borrowed_amount"])
        return total


class DebtTransaction(models.Model):
    """Individual borrowing transactions."""

    debt = models.ForeignKey(Debt, on_delete=models.CASCADE, related_name="transactions")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField(default=timezone.now)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date"]
        verbose_name_plural = "Debt transactions"

    def __str__(self):
        return f"{self.amount} borrowed for {self.debt.name} on {self.date}"

    def save(self, *args, **kwargs):
        # Update debt's borrowed_amount when transaction is saved
        if not self.pk:  # Only on creation
            self.debt.borrowed_amount += self.amount
            self.debt.save(update_fields=["borrowed_amount"])
        super().save(*args, **kwargs)
