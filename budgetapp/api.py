"""REST API viewsets for budget resources."""

from __future__ import annotations

from typing import TYPE_CHECKING

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.serializers import BaseSerializer

from budgetapp.models import Budget

from .serializers import BudgetSerializer

if TYPE_CHECKING:
    from django.db.models import QuerySet


class BudgetViewSet(viewsets.ModelViewSet):
    """ViewSet for managing budgets.

    Only returns budgets belonging to the authenticated user.
    """

    serializer_class = BudgetSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self) -> QuerySet[Budget]:
        """Return budgets for the authenticated user only."""
        return Budget.objects.filter(user=self.request.user)

    def perform_create(self, serializer: BaseSerializer[Budget]) -> None:
        """Set the user when creating a new budget."""
        serializer.save(user=self.request.user)
