from django.urls import include, path

from rest_framework.routers import DefaultRouter

from .api import BudgetViewSet
from .api_goals import GoalContributionViewSet, GoalViewSet

# Create a router and register our viewsets with it
router = DefaultRouter()
router.register(r"budgets", BudgetViewSet, basename="api-budget")
router.register(r"goals", GoalViewSet, basename="api-goal")
router.register(r"goal-contributions", GoalContributionViewSet, basename="api-goal-contribution")

# The API URLs are determined automatically by the router
urlpatterns = [
    path("", include(router.urls)),
]
