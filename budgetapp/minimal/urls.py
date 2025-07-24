from django.urls import path

from .views import (
    BudgetCreateView,
    BudgetDetailView,
    CategoryStatsView,
    ExpenseCreateUpdateView,
    ExpenseDeleteView,
    HomeView,
    IncomeUpdateView,
    SubExpenseCreateView,
    SubExpenseDeleteView,
    SubExpenseUpdateView,
    TagCreateView,
    TagDeleteView,
    TagManagementView,
    TagStatsView,
    TagUpdateView,
)

app_name = "minimal"

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("budget/<int:year>/<int:month>/", BudgetDetailView.as_view(), name="budget_detail"),
    path("budget/create/", BudgetCreateView.as_view(), name="budget_create"),
    path(
        "budget/<int:year>/<int:month>/income/update/",
        IncomeUpdateView.as_view(),
        name="income_update",
    ),
    path(
        "budget/<int:year>/<int:month>/expense/create-update/",
        ExpenseCreateUpdateView.as_view(),
        name="expense_create_update",
    ),
    path(
        "budget/<int:year>/<int:month>/expense/delete/",
        ExpenseDeleteView.as_view(),
        name="expense_delete",
    ),
    path(
        "budget/<int:year>/<int:month>/category-stats/",
        CategoryStatsView.as_view(),
        name="category_stats",
    ),
    path(
        "budget/<int:year>/<int:month>/tag-stats/",
        TagStatsView.as_view(),
        name="tag_stats",
    ),
    path(
        "budget/<int:year>/<int:month>/subexpense/create/",
        SubExpenseCreateView.as_view(),
        name="subexpense_create",
    ),
    path(
        "budget/<int:year>/<int:month>/subexpense/update/",
        SubExpenseUpdateView.as_view(),
        name="subexpense_update",
    ),
    path(
        "budget/<int:year>/<int:month>/subexpense/delete/",
        SubExpenseDeleteView.as_view(),
        name="subexpense_delete",
    ),
    # Tag management routes
    path("tags/", TagManagementView.as_view(), name="tag_management"),
    path("tags/create/", TagCreateView.as_view(), name="tag_create"),
    path("tags/update/", TagUpdateView.as_view(), name="tag_update"),
    path("tags/delete/", TagDeleteView.as_view(), name="tag_delete"),
]
