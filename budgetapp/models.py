"""Django ORM models for budgets, expenses, goals, debts, and related entities."""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
from typing import Any, Callable

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
        constraints = [
            # One budget per user per month, archived or not.
            models.UniqueConstraint(
                fields=["user", "month"],
                name="unique_budget_month_per_user",
            ),
        ]

    def __str__(self) -> str:
        return self.month.strftime("%B %Y")

    def was_edited(self) -> bool:
        """Return True if the budget was edited after creation."""
        return self.updated_at > self.created_at

    def get_gross_budgeted_expenses(self) -> Decimal:
        """Sum of expense line amounts (budgeted allocations), before returns."""
        return self.expenses.aggregate(
            total=Coalesce(Sum("amount"), Value(0), output_field=DecimalField())
        )["total"]

    def get_net_budgeted_expenses(self) -> Decimal:
        """Gross budgeted expenses minus returns (equals income − remaining)."""
        return self.get_gross_budgeted_expenses() - self.get_total_returns()

    def get_remaining_budget(self) -> Decimal:
        """Remaining after budgeted expenses, with returns credited back."""
        gross = self.get_gross_budgeted_expenses()
        total_returns = self.get_total_returns()
        return self.income - gross + total_returns

    def get_total_returns(self) -> Decimal:
        """Calculate total returns from all expenses"""
        total_returns = Decimal("0")
        for expense in self.expenses.all():
            total_returns += expense.get_total_returns()
        return total_returns

    @staticmethod
    def get_currency_choices() -> list[tuple[str, str]]:
        """Return common currency code/display pairs for form choices."""
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

    def get_summary_display_strings(
        self,
        fmt: Callable[[float | Decimal], str],
    ) -> dict[str, Any]:
        """
        Human-readable summary numbers for UI and PDF.

        Args:
            fmt: Callable taking a numeric value and returning a formatted string.
        """
        gross = self.get_gross_budgeted_expenses()
        total_ret = self.get_total_returns()
        net = self.get_net_budgeted_expenses()
        return {
            "gross_budgeted_expenses": gross,
            "total_returns_amount": total_ret,
            "net_budgeted_expenses": net,
            "budget_income_display": fmt(self.income),
            "gross_expenses_display": fmt(float(gross)),
            "total_returns_display": fmt(float(total_ret)),
            "net_expenses_display": fmt(float(net)),
            "remaining_budget_display": fmt(self.get_remaining_budget()),
        }

    def get_tag_account_breakdown(self) -> dict[str, dict[str, Any]]:
        """Per-tag totals: expense sums adjusted by transfers (out -, in +).

        Transfers do not affect remaining budget; they only reclassify which
        account tag the monthly allocation sits under.
        """
        totals: dict[int, Decimal] = {}
        meta: dict[int, dict[str, Any]] = {}

        def _ensure(tag: Tag) -> None:
            if tag.id not in meta:
                meta[tag.id] = {
                    "name": tag.name,
                    "color": tag.color,
                    "tag_id": tag.id,
                }
                totals.setdefault(tag.id, Decimal("0"))

        for expense in self.expenses.select_related("tag_foreign_key"):
            tag = expense.tag_foreign_key
            if not tag:
                continue
            _ensure(tag)
            totals[tag.id] += expense.amount

        for transfer in self.tag_transfers.select_related("from_tag", "to_tag"):
            _ensure(transfer.from_tag)
            _ensure(transfer.to_tag)
            totals[transfer.from_tag_id] -= transfer.amount
            totals[transfer.to_tag_id] += transfer.amount

        result: dict[str, dict[str, Any]] = {}
        for tag_id, amount in totals.items():
            info = meta[tag_id]
            result[info["name"]] = {
                "amount": amount,
                "tag_id": tag_id,
                "color": info["color"],
                "label": info["name"],
            }
        return result


class Category(models.Model):
    """User-defined expense category with icon and color styling."""

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
    updated_at = models.DateTimeField(auto_now=True)

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

    def __str__(self) -> str:
        return self.name

    def save(self, *args: Any, **kwargs: Any) -> None:
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

    def __str__(self) -> str:
        return self.name

    def save(self, *args: Any, **kwargs: Any) -> None:
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class TagTransfer(models.Model):
    """Zero-sum move of allocation between account tags within a budget month.

    Does not change Budget remaining; only adjusts account-tag breakdown.
    """

    budget = models.ForeignKey(
        Budget,
        on_delete=models.CASCADE,
        related_name="tag_transfers",
    )
    from_tag = models.ForeignKey(
        Tag,
        on_delete=models.CASCADE,
        related_name="transfers_out",
    )
    to_tag = models.ForeignKey(
        Tag,
        on_delete=models.CASCADE,
        related_name="transfers_in",
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField(default=timezone.now)
    note = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "Tag transfers"

    def __str__(self) -> str:
        return f"{self.amount} from {self.from_tag} to {self.to_tag} " f"({self.budget})"

    def clean(self) -> None:
        from django.core.exceptions import ValidationError

        if self.amount is not None and self.amount <= 0:
            raise ValidationError({"amount": "Amount must be greater than zero."})
        if self.from_tag_id and self.to_tag_id and self.from_tag_id == self.to_tag_id:
            raise ValidationError("Cannot transfer to the same account tag.")
        budget_user_id = self.budget.user_id if self.budget_id else None
        if budget_user_id and self.from_tag_id and self.from_tag.user_id != budget_user_id:
            raise ValidationError({"from_tag": "Tag must belong to the budget owner."})
        if budget_user_id and self.to_tag_id and self.to_tag.user_id != budget_user_id:
            raise ValidationError({"to_tag": "Tag must belong to the budget owner."})

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.full_clean()
        super().save(*args, **kwargs)


class Expense(models.Model):
    """Budget expense line item; may have sub-expenses and an optional bill reminder."""

    budget = models.ForeignKey(Budget, on_delete=models.CASCADE, related_name="expenses")
    name = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    is_recurring = models.BooleanField(default=False)
    is_daily = models.BooleanField(
        default=False,
        help_text="Day-to-day spending line (groceries, transport); used for Safe to spend today",
    )
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
    bill_reminder = models.ForeignKey(
        "BillReminder",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="linked_expenses",
        help_text="Optional scheduled bill used for reminders and dashboard banner",
    )

    def __str__(self) -> str:
        return f"{self.name} - {self.amount}"

    def get_remaining_amount(self) -> Decimal:
        """Return unspent amount after all sub-expenses (including returns)."""
        sub_expenses = self.sub_expenses.all()
        total_spent = sub_expenses.aggregate(total=models.Sum("amount"))["total"] or Decimal("0")
        return self.amount - total_spent

    def get_total_returns(self) -> Decimal:
        """Sum sub-expenses marked as returns/refunds."""
        total_returns = self.sub_expenses.filter(is_return=True).aggregate(
            total=models.Sum("amount")
        )["total"] or Decimal("0")
        return total_returns

    def get_net_amount(self) -> Decimal:
        """Return the net amount (amount minus returns) for this expense."""
        return self.amount - self.get_remaining_amount()

    @property
    def subexpense_total(self) -> Decimal | int:
        """Sum of non-return sub-expenses."""
        return (
            self.sub_expenses.filter(is_return=False).aggregate(total=models.Sum("amount"))["total"]
            or 0
        )


class BillReminder(models.Model):
    """
    Scheduled non-monthly bill (for example annual tax) with dashboard alerts
    and optional auto-insert into the budget for its due month.
    """

    class Severity(models.TextChoices):
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="bill_reminders",
        null=True,
        blank=True,
    )
    name = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0"))
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="bill_reminders",
    )
    tag = models.ForeignKey(
        Tag,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="bill_reminders",
    )
    next_bill_date = models.DateField()
    remind_days_before = models.PositiveIntegerField(
        default=30,
        help_text="How many days before the due date the alert window starts",
    )
    severity = models.CharField(
        max_length=10,
        choices=Severity.choices,
        default=Severity.MEDIUM,
    )
    recurrence_months = models.PositiveIntegerField(
        default=12,
        help_text="How many months to advance the due date after it is applied to a budget",
    )
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["next_bill_date", "name"]
        indexes = [
            models.Index(fields=["user", "is_active", "next_bill_date"]),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.next_bill_date})"


class SubExpense(models.Model):
    """Partial spend or return/refund against a parent expense line item."""

    expense = models.ForeignKey(Expense, on_delete=models.CASCADE, related_name="sub_expenses")
    name = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    is_return = models.BooleanField(
        default=False,
        help_text="Mark as return/refund to add this amount back to the remaining budget",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        prefix = "Return: " if self.is_return else ""
        return f"{prefix}{self.name} - {self.amount}"


class BudgetLog(models.Model):
    """Audit log entry for budget create/update/delete actions."""

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

    def __str__(self) -> str:
        return f"{self.get_action_display()} - {self.month.strftime('%B %Y')}"


class ArchivedBudget(models.Model):
    """Link table marking a budget as archived with a timestamp."""

    budget = models.OneToOneField("Budget", on_delete=models.CASCADE)
    archived_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-budget__month"]

    def __str__(self) -> str:
        return f"Archive: {self.budget.month.strftime('%Y-%m')}"


class BudgetDeletionLog(models.Model):
    """Soft-delete audit record with expiry for budget recovery windows."""

    month = models.DateField()
    deleted_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    class Meta:
        ordering = ["-deleted_at"]

    def __str__(self) -> str:
        return (
            f"Budget for {self.month.strftime('%B %Y')} "
            f"deleted on {self.deleted_at.strftime('%Y-%m-%d %H:%M')}"
        )


class IncomeHistory(models.Model):
    """Historical record of income or currency changes on a budget."""

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

    def __str__(self) -> str:
        return f"Income change for {self.budget.month.strftime('%B %Y')}"


class RecentUpdate(models.Model):
    """Activity feed entry for recent budget changes."""

    budget = models.ForeignKey("Budget", on_delete=models.CASCADE, related_name="recent_updates")
    action_type = models.CharField(max_length=50)  # e.g., 'expense_added', 'income_updated'
    description = models.TextField()
    timestamp = models.DateTimeField(default=timezone.now)
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    category = models.ForeignKey("Category", on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ["-timestamp"]

    def __str__(self) -> str:
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

    def __str__(self) -> str:
        return self.name

    @property
    def progress_percentage(self) -> int:
        """Return the percentage of progress towards the goal."""
        if self.target_amount == 0:
            return 100
        return min(100, int((self.current_amount / self.target_amount) * 100))

    def get_average_contribution(self) -> tuple[Decimal | float, float | int | None]:
        """Calculate average contribution amount and frequency in days."""
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

    def get_projected_completion(self) -> tuple[date | None, Decimal | float, bool]:
        """Project completion date, monthly rate, and on-target status."""
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
        projected_date = timezone.now().date() + timedelta(days=int(days_needed))

        # Determine if we're on target (if target date exists)
        is_on_target = True
        if self.target_date:
            is_on_target = projected_date <= self.target_date

        return projected_date, monthly_rate, is_on_target

    def is_on_track(self) -> bool | None:
        """Return whether the goal is on pace to meet its target date."""
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

    def monthly_contribution_needed(self) -> Decimal | None:
        """Return monthly savings needed to reach the goal by the target date."""
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

    def __str__(self) -> str:
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

    def __str__(self) -> str:
        return f"{self.name} - {self.borrowed_amount}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        is_new = self.pk is None  # noqa: F841

        super().save(*args, **kwargs)

        if not self.debt_tag and self.name:
            tag_name = self.generate_debt_tag_name()
            self.debt_tag = Tag.objects.create(
                user=self.user,
                name=tag_name,
                description=f"Tracking tag for debt: {self.name}",
                color="#ff5722",
            )
            super().save(update_fields=["debt_tag"])

    def generate_debt_tag_name(self) -> str:
        """Generate a unique tag name for debt expense tracking."""
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
    def repaid_amount(self) -> Decimal:
        """Calculate total repaid from expenses tagged with this debt."""
        return self.debt_tag.expenses.aggregate(total=models.Sum("amount"))["total"] or Decimal("0")

    @property
    def remaining_to_repay(self) -> Decimal:
        """Amount still owed after repayments recorded via tagged expenses."""
        return self.borrowed_amount - self.repaid_amount

    @property
    def repayment_progress_percentage(self) -> int:
        """Repayment progress as a percentage of borrowed amount."""
        if self.borrowed_amount == 0:
            return 0
        return min(100, int((self.repaid_amount / self.borrowed_amount) * 100))

    @property
    def progress_percentage(self) -> int:
        """Borrowing progress as a percentage of the total credit line."""
        if self.total_amount == 0:
            return 0
        return min(100, int((self.borrowed_amount / self.total_amount) * 100))

    @property
    def is_fully_repaid(self) -> bool:
        """Return True when repayments meet or exceed the borrowed amount."""
        return self.repaid_amount >= self.borrowed_amount

    def check_and_update_status(self) -> bool:
        """Deactivate the debt tag when the debt is fully repaid."""
        if self.is_fully_repaid and self.debt_tag.is_active:
            self.debt_tag.is_active = False
            self.debt_tag.save()
            return True
        return False

    def recalculate_borrowed_amount(self) -> Decimal:
        """Recalculate ``borrowed_amount`` from related transactions."""
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

    def __str__(self) -> str:
        return f"{self.amount} borrowed for {self.debt.name} on {self.date}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        if not self.pk:
            self.debt.borrowed_amount += self.amount
            self.debt.save(update_fields=["borrowed_amount"])
        super().save(*args, **kwargs)


class PushSubscription(models.Model):
    """A browser (phone or PC) that asked for bill alerts by Web Push."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="push_subscriptions"
    )
    endpoint = models.URLField(max_length=500, unique=True)
    p256dh = models.CharField(max_length=200)
    auth = models.CharField(max_length=100)
    user_agent = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_alert_on = models.DateField(
        null=True, blank=True, help_text="The day the last bill alert went to this browser"
    )

    def __str__(self) -> str:
        return f"Push subscription of {self.user} ({self.user_agent or 'browser'})"


class WebPushKey(models.Model):
    """The server's VAPID key pair for Web Push. monAI makes it on first use; there is 1 row."""

    private_key = models.TextField(help_text="PEM. Keep it secret.")
    public_key = models.CharField(max_length=200, help_text="URL-safe base64, for the browser")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"Web Push key from {self.created_at:%Y-%m-%d}"
