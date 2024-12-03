from django.urls import path
from .views import HomeView, budget_detail, expense_detail, create_next_budget

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('budget/<int:year>/<int:month>/', budget_detail, name='budget_detail'),
    path('expense/<int:expense_id>/', expense_detail, name='expense_detail'),
    path('create-next-budget/', create_next_budget, name='create_next_budget'),
] 