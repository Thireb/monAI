"""URL routing for the budget REST and mobile sync API."""

from __future__ import annotations

from django.urls import URLPattern, URLResolver, include, path

from rest_framework.routers import DefaultRouter

from .api import BudgetViewSet
from .api_goals import GoalContributionViewSet, GoalViewSet
from .api_mobile_auth import MobileObtainAuthTokenView
from .api_mobile_catalog import (
    MobileBillReminderPullView,
    MobileBillReminderPushView,
    MobileCategoryPullView,
    MobileCategoryPushView,
    MobileExpensePullView,
    MobileExpensePushView,
    MobileSubExpensePullView,
    MobileSubExpensePushView,
    MobileTagPullView,
    MobileTagPushView,
    MobileTagTransferPullView,
    MobileTagTransferPushView,
)
from .api_mobile_sync import MobileBudgetPullView, MobileBudgetPushView
from .views_health import mobile_health

router = DefaultRouter()
router.register(r"budgets", BudgetViewSet, basename="api-budget")
router.register(r"goals", GoalViewSet, basename="api-goal")
router.register(r"goal-contributions", GoalContributionViewSet, basename="api-goal-contribution")

urlpatterns: list[URLPattern | URLResolver] = [
    path("health/", mobile_health, name="api-health"),
    path("mobile/auth/token/", MobileObtainAuthTokenView.as_view(), name="api-mobile-token"),
    path("mobile/budgets/pull/", MobileBudgetPullView.as_view(), name="api-mobile-budget-pull"),
    path("mobile/budgets/push/", MobileBudgetPushView.as_view(), name="api-mobile-budget-push"),
    path(
        "mobile/categories/pull/",
        MobileCategoryPullView.as_view(),
        name="api-mobile-category-pull",
    ),
    path(
        "mobile/categories/push/",
        MobileCategoryPushView.as_view(),
        name="api-mobile-category-push",
    ),
    path("mobile/tags/pull/", MobileTagPullView.as_view(), name="api-mobile-tag-pull"),
    path("mobile/tags/push/", MobileTagPushView.as_view(), name="api-mobile-tag-push"),
    path(
        "mobile/expenses/pull/",
        MobileExpensePullView.as_view(),
        name="api-mobile-expense-pull",
    ),
    path(
        "mobile/expenses/push/",
        MobileExpensePushView.as_view(),
        name="api-mobile-expense-push",
    ),
    path(
        "mobile/sub-expenses/pull/",
        MobileSubExpensePullView.as_view(),
        name="api-mobile-subexpense-pull",
    ),
    path(
        "mobile/sub-expenses/push/",
        MobileSubExpensePushView.as_view(),
        name="api-mobile-subexpense-push",
    ),
    path(
        "mobile/bill-reminders/pull/",
        MobileBillReminderPullView.as_view(),
        name="api-mobile-bill-reminder-pull",
    ),
    path(
        "mobile/bill-reminders/push/",
        MobileBillReminderPushView.as_view(),
        name="api-mobile-bill-reminder-push",
    ),
    path(
        "mobile/tag-transfers/pull/",
        MobileTagTransferPullView.as_view(),
        name="api-mobile-tag-transfer-pull",
    ),
    path(
        "mobile/tag-transfers/push/",
        MobileTagTransferPushView.as_view(),
        name="api-mobile-tag-transfer-push",
    ),
    path("", include(router.urls)),
]
