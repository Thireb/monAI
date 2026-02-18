from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from budgetapp.models import Budget

from .serializers import BudgetSerializer


class BudgetViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing budgets.
    Only returns budgets belonging to the authenticated user.
    """

    serializer_class = BudgetSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return budgets for the authenticated user only."""
        return Budget.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        """Set the user when creating a new budget."""
        serializer.save(user=self.request.user)
