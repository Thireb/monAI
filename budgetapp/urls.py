from django.urls import path
from .views import HomeView, budget_detail, expense_detail

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('budget/<int:year>/<int:month>/', budget_detail, name='budget_detail'),
    path('expense/<int:expense_id>/', expense_detail, name='expense_detail'),
] 