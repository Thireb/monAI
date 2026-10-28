"""REST API viewsets for budget resources."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer

from budgetapp.models import Budget
from budgetapp.services.export import build_budget_export

from .serializers import BudgetSerializer

if TYPE_CHECKING:
    from django.db.models import QuerySet
    from rest_framework.request import Request


class BudgetViewSet(viewsets.ModelViewSet):
    """ViewSet for managing budgets.

    Only returns budgets belonging to the authenticated user.
    """

    serializer_class = BudgetSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self) -> QuerySet[Budget]:
        """Return budgets for the authenticated user only."""
        return Budget.objects.filter(user=self.request.user)

    def _free_month(self, serializer: BaseSerializer[Budget]) -> dict[str, Any]:
        """Return the month to save (day 1) as save arguments; 400 when the month is taken."""
        month = serializer.validated_data.get("month")  # type: ignore[union-attr]
        if month is None:
            return {}
        month = month.replace(day=1)
        others = Budget.objects.filter(user=self.request.user, month=month)
        if serializer.instance is not None:
            others = others.exclude(pk=serializer.instance.pk)
        if others.exists():
            raise ValidationError({"month": ["You already have a budget for this month."]})
        return {"month": month}

    def perform_create(self, serializer: BaseSerializer[Budget]) -> None:
        """Set the user when creating a new budget."""
        serializer.save(user=self.request.user, **self._free_month(serializer))

    def perform_update(self, serializer: BaseSerializer[Budget]) -> None:
        """Save the budget unless its new month is taken."""
        serializer.save(**self._free_month(serializer))

    @action(detail=True, methods=["get"])
    def export(self, request: Request, pk: str | None = None) -> Response:
        """Return 1 budget, with its expenses and sub-expenses, as portable JSON."""
        budget = self.get_object()
        return Response(build_budget_export(budget))
