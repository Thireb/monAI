"""
Views package for the minimal theme.

This package splits views into logical modules for better organization.
All views are re-exported here for backwards compatibility.
"""

from __future__ import annotations

# Base views and utilities
from .base import (
    LoginRequiredTemplateView,
    LoginRequiredView,
    OfflineView,
    UnicodeJsonResponse,
)

# Home and calendar views
from .home import CalendarContentView, HomeView

from .bill_reminder import (
    BillReminderDefaultsView,
    BillReminderDeleteView,
    BillReminderListView,
    BillReminderSaveView,
)

# Budget views
from .budget import (
    BudgetCreateView,
    BudgetDeleteView,
    BudgetDetailView,
    BudgetEmailPDFView,
    IncomeUpdateView,
    SummaryCardsView,
)

# Expense views
from .expense import (
    ExpenseCreateUpdateView,
    ExpenseDeleteView,
)

# SubExpense views
from .subexpense import (
    SubExpenseCreateView,
    SubExpenseDeleteView,
    SubExpenseUpdateView,
)

# Stats views
from .stats import CategoryStatsView, TagStatsView

# Tag views
from .tag import (
    TagCreateView,
    TagDeleteView,
    TagManagementView,
    TagUpdateView,
)

# Category views
from .category import (
    CategoryCreateView,
    CategoryDeleteView,
    CategoryListView,
    CategoryManagementView,
    CategoryUpdateView,
)

# Debt views
from .debt import (
    DebtBorrowingView,
    DebtCreateView,
    DebtDeleteView,
    DebtDetailView,
    DebtListView,
    DebtTransactionDeleteView,
    DebtTransactionUpdateView,
    DebtUpdateView,
)

# Goal views
from .goal import (
    GoalContributionCreateView,
    GoalContributionDeleteView,
    GoalContributionUpdateView,
    GoalCreateView,
    GoalDeleteView,
    GoalDetailView,
    GoalListView,
    GoalUpdateView,
)

__all__ = [
    # Base
    "LoginRequiredView",
    "LoginRequiredTemplateView",
    "UnicodeJsonResponse",
    "OfflineView",
    # Home
    "HomeView",
    "CalendarContentView",
    # Budget
    "BudgetDetailView",
    "BudgetCreateView",
    "BudgetDeleteView",
    "BudgetEmailPDFView",
    "IncomeUpdateView",
    "SummaryCardsView",
    # Expense
    "ExpenseCreateUpdateView",
    "ExpenseDeleteView",
    # SubExpense
    "SubExpenseCreateView",
    "SubExpenseUpdateView",
    "SubExpenseDeleteView",
    # Stats
    "CategoryStatsView",
    "TagStatsView",
    # Tag
    "TagManagementView",
    "TagCreateView",
    "TagUpdateView",
    "TagDeleteView",
    # Category
    "CategoryManagementView",
    "CategoryListView",
    "CategoryCreateView",
    "CategoryUpdateView",
    "CategoryDeleteView",
    # Debt
    "DebtListView",
    "DebtDetailView",
    "DebtCreateView",
    "DebtUpdateView",
    "DebtDeleteView",
    "DebtBorrowingView",
    "DebtTransactionUpdateView",
    "DebtTransactionDeleteView",
    # Goals
    "GoalListView",
    "GoalDetailView",
    "GoalCreateView",
    "GoalUpdateView",
    "GoalDeleteView",
    "GoalContributionCreateView",
    "GoalContributionUpdateView",
    "GoalContributionDeleteView",
    # Bill reminders
    "BillReminderListView",
    "BillReminderSaveView",
    "BillReminderDeleteView",
    "BillReminderDefaultsView",
]
