from django.urls import path

from .views import BudgetDetailView, HomeView

urlpatterns = [
    path("", HomeView.as_view(), name="minimal_home"),
    path(
        "budget/<int:year>/<int:month>/", BudgetDetailView.as_view(), name="minimal_budget_detail"
    ),
]
