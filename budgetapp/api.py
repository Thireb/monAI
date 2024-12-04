from budgetapp.models import Budget
from rest_framework import viewsets
from .serializers import BudgetSerializer, ExpenseSerializer

class BudgetViewSet(viewsets.ModelViewSet):
    queryset = Budget.objects.all()
    serializer_class = BudgetSerializer 