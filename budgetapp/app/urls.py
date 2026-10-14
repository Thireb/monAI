"""URL routes for the new UI (/app/)."""

from __future__ import annotations

from django.urls import URLPattern, path

from .views.goals import (
    DebtBorrowView,
    DebtCreateView,
    DebtRepayView,
    GoalContributeView,
    GoalCreateView,
    GoalsPanelView,
    GoalsView,
)
from .views.home import HomeView
from .views.line import (
    LineCreateView,
    LineDailyToggleView,
    LineDeleteView,
    LineSheetView,
    LineSpendCreateView,
    SpendDeleteView,
)
from .views.month import MonthBillsApplyView, MonthCreateView, MonthPanelView, MonthView
from .views.spend import SpendCreateView, SpendUndoView

app_name = "app"

urlpatterns: list[URLPattern] = [
    path("", HomeView.as_view(), name="home"),
    path("month/<int:year>/<int:month>/", MonthView.as_view(), name="month"),
    path("month/<int:year>/<int:month>/panel/", MonthPanelView.as_view(), name="month_panel"),
    path("month/<int:year>/<int:month>/create/", MonthCreateView.as_view(), name="month_create"),
    path(
        "month/<int:year>/<int:month>/bills/",
        MonthBillsApplyView.as_view(),
        name="month_bills_apply",
    ),
    path("month/<int:year>/<int:month>/lines/", LineCreateView.as_view(), name="line_create"),
    path("lines/<int:pk>/", LineSheetView.as_view(), name="line_sheet"),
    path("lines/<int:pk>/daily/", LineDailyToggleView.as_view(), name="line_daily"),
    path("lines/<int:pk>/delete/", LineDeleteView.as_view(), name="line_delete"),
    path("lines/<int:pk>/spends/", LineSpendCreateView.as_view(), name="line_spend_create"),
    path("goals/", GoalsView.as_view(), name="goals"),
    path("goals/panel/", GoalsPanelView.as_view(), name="goals_panel"),
    path("goals/new/", GoalCreateView.as_view(), name="goal_create"),
    path("goals/<int:pk>/contribute/", GoalContributeView.as_view(), name="goal_contribute"),
    path("debts/new/", DebtCreateView.as_view(), name="debt_create"),
    path("debts/<int:pk>/repay/", DebtRepayView.as_view(), name="debt_repay"),
    path("debts/<int:pk>/borrow/", DebtBorrowView.as_view(), name="debt_borrow"),
    path("spends/", SpendCreateView.as_view(), name="spend_create"),
    path("spends/<int:pk>/undo/", SpendUndoView.as_view(), name="spend_undo"),
    path("spends/<int:pk>/delete/", SpendDeleteView.as_view(), name="spend_delete"),
]
