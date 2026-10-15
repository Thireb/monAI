"""URL routing for the budget REST API and the health check."""

from __future__ import annotations

from django.urls import URLPattern, URLResolver, include, path

from rest_framework.routers import DefaultRouter

from .api import BudgetViewSet
from .api_goals import GoalContributionViewSet, GoalViewSet
from .views_health import health

router = DefaultRouter()
router.register(r"budgets", BudgetViewSet, basename="api-budget")
router.register(r"goals", GoalViewSet, basename="api-goal")
router.register(r"goal-contributions", GoalContributionViewSet, basename="api-goal-contribution")

urlpatterns: list[URLPattern | URLResolver] = [
    path("health/", health, name="api-health"),
    path("", include(router.urls)),
]
