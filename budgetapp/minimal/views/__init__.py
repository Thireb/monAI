"""
Views package for the minimal theme.

This package splits views into logical modules for better organization.
All views are re-exported here for backwards compatibility.
"""

# Base views and utilities
from .base import (
    LoginRequiredTemplateView,
    LoginRequiredView,
    OfflineView,
    UnicodeJsonResponse,
)

# Home and calendar views
from .home import CalendarContentView, HomeView

# Budget views
from .budget import (
    BudgetCreateView,
    BudgetDeleteView,
    BudgetDetailView,
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
]

