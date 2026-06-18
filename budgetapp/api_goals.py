"""REST API viewsets for financial goals and contributions."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from django.db.models import QuerySet, Sum
from datetime import timedelta

from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer

from .models import Goal, GoalContribution
from .serializers import GoalContributionSerializer, GoalDetailSerializer, GoalSerializer


class GoalViewSet(viewsets.ModelViewSet):
    """ViewSet for managing financial goals.

    Only returns goals belonging to the authenticated user.
    """

    serializer_class = GoalSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self) -> QuerySet[Goal]:
        """Return goals for the authenticated user only."""
        return Goal.objects.filter(user=self.request.user)

    def get_serializer_class(self) -> type[BaseSerializer[Any]]:
        """Use the detail serializer for retrieve/detail actions."""
        if self.action in ["retrieve", "detail"]:
            return GoalDetailSerializer
        return GoalSerializer

    def perform_create(self, serializer: BaseSerializer[Goal]) -> None:
        """Set the user when creating a new goal."""
        serializer.save(user=self.request.user)

    @action(detail=True, methods=["get"])
    def statistics(self, request: Request, pk: int | None = None) -> Response:
        """Return detailed progress statistics for a single goal.

        Args:
            request: Incoming HTTP request.
            pk: Primary key of the goal (provided by the router).

        Returns:
            JSON payload with averages, consistency, and progress-by-month data.
        """
        goal = self.get_object()

        contributions = goal.contributions.all()
        total_contributions = contributions.aggregate(total=Sum("amount"))["total"] or 0

        first_contribution = contributions.order_by("date").first()
        start_date = first_contribution.date if first_contribution else goal.start_date

        today = timezone.now().date()
        months_passed = (today.year - start_date.year) * 12 + today.month - start_date.month
        months_passed = max(1, months_passed)

        average_monthly = total_contributions / months_passed

        month_count: dict[str, int] = {}
        for contrib in contributions:
            key = f"{contrib.date.year}-{contrib.date.month}"
            month_count[key] = month_count.get(key, 0) + 1

        consistency = (len(month_count) / months_passed) * 100 if months_passed > 0 else 0

        progress_by_month: list[dict[str, str]] = []
        running_total = Decimal("0")

        for year in range(start_date.year, today.year + 1):
            for month in range(1, 13):
                if year == start_date.year and month < start_date.month:
                    continue
                if year == today.year and month > today.month:
                    continue

                month_contribs = sum(
                    c.amount for c in contributions if c.date.year == year and c.date.month == month
                )

                running_total += month_contribs
                progress_by_month.append(
                    {
                        "month": f"{year}-{month:02d}",
                        "amount": str(running_total),
                    }
                )

        is_on_track = goal.is_on_track()

        projected_days: int | None = None
        days_behind_schedule: int | None = None

        if average_monthly > 0 and goal.target_amount > goal.current_amount:
            amount_remaining = goal.target_amount - goal.current_amount
            months_remaining = amount_remaining / average_monthly
            projected_days = int(months_remaining * 30)

            if goal.target_date:
                days_to_target = (goal.target_date - today).days
                if days_to_target < projected_days:
                    days_behind_schedule = projected_days - days_to_target

        response_data: dict[str, Any] = {
            "goal_id": goal.id,
            "goal_name": goal.name,
            "average_monthly_contribution": str(round(average_monthly, 2)),
            "contribution_consistency": round(consistency, 1),
            "on_track": is_on_track,
            "monthly_contribution_needed": str(goal.monthly_contribution_needed() or 0),
            "progress_by_month": progress_by_month,
        }

        if projected_days is not None:
            projected_date = today + timedelta(days=projected_days)
            response_data["projected_completion_date"] = projected_date.isoformat()

            if days_behind_schedule is not None:
                response_data["days_behind_schedule"] = days_behind_schedule

        return Response(response_data)

    @action(detail=True, methods=["post"])
    def add_contribution(self, request: Request, pk: int | None = None) -> Response:
        """Add a contribution to a goal and update its current amount.

        Args:
            request: Request body with contribution fields.
            pk: Primary key of the goal (provided by the router).

        Returns:
            Serialized contribution on success, or validation errors.
        """
        goal = self.get_object()

        serializer = GoalContributionSerializer(data=request.data)
        if serializer.is_valid():
            contribution = serializer.save(goal=goal)

            goal.current_amount += contribution.amount
            goal.save(update_fields=["current_amount"])

            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GoalContributionViewSet(viewsets.ModelViewSet):
    """ViewSet for managing goal contributions.

    Only returns contributions for goals belonging to the authenticated user.
    """

    serializer_class = GoalContributionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self) -> QuerySet[GoalContribution]:
        """Return contributions for the user's goals, optionally filtered by goal."""
        goal_id = self.request.query_params.get("goal", None)
        queryset = GoalContribution.objects.filter(goal__user=self.request.user)
        if goal_id:
            queryset = queryset.filter(goal_id=goal_id)
        return queryset

    def perform_create(self, serializer: BaseSerializer[GoalContribution]) -> None:
        """Save a contribution and update the parent goal's current amount."""
        goal = serializer.validated_data.get("goal")
        if goal.user != self.request.user:
            raise PermissionDenied("You can only add contributions to your own goals.")

        contribution = serializer.save()

        goal = contribution.goal
        goal.current_amount += contribution.amount
        goal.save(update_fields=["current_amount"])

    def perform_update(self, serializer: BaseSerializer[GoalContribution]) -> None:
        """Adjust the goal's current amount when a contribution is edited."""
        old_amount = self.get_object().amount

        contribution = serializer.save()

        goal = contribution.goal
        goal.current_amount = goal.current_amount - old_amount + contribution.amount
        goal.save(update_fields=["current_amount"])

    def perform_destroy(self, instance: GoalContribution) -> None:
        """Reduce the goal's current amount when a contribution is deleted."""
        goal = instance.goal
        amount = instance.amount

        instance.delete()

        goal.current_amount -= amount
        goal.save(update_fields=["current_amount"])
