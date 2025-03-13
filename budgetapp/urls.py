from django.urls import path

from .views import (
    HomeView,
    add_contribution,
    archive_budget,
    budget_detail,
    category_delete,
    category_edit,
    category_list,
    create_next_budget,
    delete_archived_budget,
    delete_budget,
    expense_detail,
    get_next_month,
    goal_create,
    goal_delete,
    goal_detail,
    goal_edit,
    goal_list,
    view_archives,
)

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("budget/<int:year>/<int:month>/", budget_detail, name="budget_detail"),
    path("expense/<int:expense_id>/", expense_detail, name="expense_detail"),
    path("create-next-budget/", create_next_budget, name="create_next_budget"),
    path("budget/delete/<str:year_month>/", delete_budget, name="delete_budget"),
    path("get-next-month/", get_next_month, name="get_next_month"),
    path("budget/archive/<str:year_month>/", archive_budget, name="archive_budget"),
    path("archives/", view_archives, name="view_archives"),
    path(
        "archives/delete/<str:year_month>/", delete_archived_budget, name="delete_archived_budget"
    ),
    path("categories/", category_list, name="category_list"),
    path("categories/<slug:slug>/edit/", category_edit, name="category_edit"),
    path("categories/<slug:slug>/delete/", category_delete, name="category_delete"),
    # Goals URLs
    path("goals/", goal_list, name="goal_list"),
    path("goals/<int:goal_id>/", goal_detail, name="goal_detail"),
    path("goals/create/", goal_create, name="goal_create"),
    path("goals/<int:goal_id>/edit/", goal_edit, name="goal_edit"),
    path("goals/<int:goal_id>/delete/", goal_delete, name="goal_delete"),
    path("goals/<int:goal_id>/contribute/", add_contribution, name="add_contribution"),
]
