from rest_framework import viewsets

from budgetapp.models import Budget

from .serializers import BudgetSerializer, ExpenseSerializer


class BudgetViewSet(viewsets.ModelViewSet):
    queryset = Budget.objects.all()
    serializer_class = BudgetSerializer
