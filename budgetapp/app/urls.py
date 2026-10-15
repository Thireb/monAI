"""URL routes for the new UI (/app/)."""

from __future__ import annotations

from django.urls import URLPattern, path

from .views.goals import (
    BorrowingDeleteView,
    ContributionDeleteView,
    DebtBorrowView,
    DebtDeleteView,
    DebtSheetView,
    GoalDeleteView,
    GoalSheetView,
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
from .views.manage import ItemDeleteView, ItemSheetView, ManagePanelView, ManageView
from .views.month import (
    MonthBillsApplyView,
    MonthCreateView,
    MonthPanelView,
    MonthsView,
    MonthView,
    RecapView,
)
from .views.offline import OfflineUrlsView, OfflineView
from .views.month_settings import (
    IncomeUpdateView,
    MonthDeleteView,
    MonthEmailView,
    TransferCreateView,
    TransferDeleteView,
)
from .views.push import PushKeyView, PushSubscribeView, PushTestView, PushUnsubscribeView
from .views.spend import SpendCreateView, SpendUndoView

app_name = "app"

urlpatterns: list[URLPattern] = [
    path("", HomeView.as_view(), name="home"),
    path("months/", MonthsView.as_view(), name="months"),
    path("month/<int:year>/<int:month>/", MonthView.as_view(), name="month"),
    path("month/<int:year>/<int:month>/recap/", RecapView.as_view(), name="recap"),
    path("month/<int:year>/<int:month>/panel/", MonthPanelView.as_view(), name="month_panel"),
    path("month/<int:year>/<int:month>/create/", MonthCreateView.as_view(), name="month_create"),
    path(
        "month/<int:year>/<int:month>/bills/",
        MonthBillsApplyView.as_view(),
        name="month_bills_apply",
    ),
    path("month/<int:year>/<int:month>/income/", IncomeUpdateView.as_view(), name="income_update"),
    path(
        "month/<int:year>/<int:month>/transfers/",
        TransferCreateView.as_view(),
        name="transfer_create",
    ),
    path("month/<int:year>/<int:month>/email/", MonthEmailView.as_view(), name="month_email"),
    path("month/<int:year>/<int:month>/delete/", MonthDeleteView.as_view(), name="month_delete"),
    path("transfers/<int:pk>/delete/", TransferDeleteView.as_view(), name="transfer_delete"),
    path("month/<int:year>/<int:month>/lines/", LineCreateView.as_view(), name="line_create"),
    path("lines/<int:pk>/", LineSheetView.as_view(), name="line_sheet"),
    path("lines/<int:pk>/daily/", LineDailyToggleView.as_view(), name="line_daily"),
    path("lines/<int:pk>/delete/", LineDeleteView.as_view(), name="line_delete"),
    path("lines/<int:pk>/spends/", LineSpendCreateView.as_view(), name="line_spend_create"),
    path("goals/", GoalsView.as_view(), name="goals"),
    path("goals/panel/", GoalsPanelView.as_view(), name="goals_panel"),
    path("goals/new/", GoalCreateView.as_view(), name="goal_create"),
    path("goals/<int:pk>/contribute/", GoalContributeView.as_view(), name="goal_contribute"),
    path("goals/<int:pk>/", GoalSheetView.as_view(), name="goal_sheet"),
    path("goals/<int:pk>/delete/", GoalDeleteView.as_view(), name="goal_delete"),
    path(
        "contributions/<int:pk>/delete/",
        ContributionDeleteView.as_view(),
        name="contribution_delete",
    ),
    path("debts/<int:pk>/", DebtSheetView.as_view(), name="debt_sheet"),
    path("debts/<int:pk>/delete/", DebtDeleteView.as_view(), name="debt_delete"),
    path("borrowings/<int:pk>/delete/", BorrowingDeleteView.as_view(), name="borrowing_delete"),
    path("debts/new/", DebtCreateView.as_view(), name="debt_create"),
    path("debts/<int:pk>/repay/", DebtRepayView.as_view(), name="debt_repay"),
    path("debts/<int:pk>/borrow/", DebtBorrowView.as_view(), name="debt_borrow"),
    path("more/", ManageView.as_view(), name="manage"),
    path("more/panel/", ManagePanelView.as_view(), name="manage_panel"),
    path("more/<str:kind>/new/", ItemSheetView.as_view(), name="manage_new"),
    path("more/<str:kind>/<int:pk>/", ItemSheetView.as_view(), name="manage_item"),
    path("more/<str:kind>/<int:pk>/delete/", ItemDeleteView.as_view(), name="manage_delete"),
    path("offline/", OfflineView.as_view(), name="offline"),
    path("offline/urls/", OfflineUrlsView.as_view(), name="offline_urls"),
    path("push/key/", PushKeyView.as_view(), name="push_key"),
    path("push/subscribe/", PushSubscribeView.as_view(), name="push_subscribe"),
    path("push/unsubscribe/", PushUnsubscribeView.as_view(), name="push_unsubscribe"),
    path("push/test/", PushTestView.as_view(), name="push_test"),
    path("spends/", SpendCreateView.as_view(), name="spend_create"),
    path("spends/<int:pk>/undo/", SpendUndoView.as_view(), name="spend_undo"),
    path("spends/<int:pk>/delete/", SpendDeleteView.as_view(), name="spend_delete"),
]
