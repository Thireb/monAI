from django.urls import include, path

from rest_framework.routers import DefaultRouter

from .api import BudgetViewSet
from .api_goals import GoalContributionViewSet, GoalViewSet
from .api_mobile_auth import MobileObtainAuthTokenView
from .api_mobile_sync import MobileBudgetPullView, MobileBudgetPushView
from .views_health import mobile_health

# Create a router and register our viewsets with it
router = DefaultRouter()
router.register(r"budgets", BudgetViewSet, basename="api-budget")
router.register(r"goals", GoalViewSet, basename="api-goal")
router.register(r"goal-contributions", GoalContributionViewSet, basename="api-goal-contribution")

# The API URLs are determined automatically by the router
urlpatterns = [
    path("health/", mobile_health, name="api-health"),
    path("mobile/auth/token/", MobileObtainAuthTokenView.as_view(), name="api-mobile-token"),
    path("mobile/budgets/pull/", MobileBudgetPullView.as_view(), name="api-mobile-budget-pull"),
    path("mobile/budgets/push/", MobileBudgetPushView.as_view(), name="api-mobile-budget-push"),
    path("", include(router.urls)),
]
