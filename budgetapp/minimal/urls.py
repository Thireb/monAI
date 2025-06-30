from django.urls import path

from .views import (
    BudgetCreateView,
    BudgetDetailView,
    CategoryStatsView,
    ExpenseCreateUpdateView,
    ExpenseDeleteView,
    HomeView,
    IncomeUpdateView,
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
]
