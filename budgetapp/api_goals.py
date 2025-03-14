from django.db.models import Sum
from django.utils import timezone

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Goal, GoalContribution
from .serializers import GoalContributionSerializer, GoalDetailSerializer, GoalSerializer


class GoalViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing financial goals.
    """

    serializer_class = GoalSerializer

    def get_queryset(self):
        """
        Return all goals without filtering by user.
        """
        return Goal.objects.all()

    def get_serializer_class(self):
        if self.action in ["retrieve", "detail"]:
            return GoalDetailSerializer
        return GoalSerializer

    @action(detail=True, methods=["get"])
    def statistics(self, request, pk=None):
        """
        Get detailed statistics about a goal's progress.
        """
        goal = self.get_object()

        # Calculate average monthly contribution
        contributions = goal.contributions.all()
        total_contributions = contributions.aggregate(total=Sum("amount"))["total"] or 0

        # Get first contribution date or start date
        first_contribution = contributions.order_by("date").first()
        start_date = first_contribution.date if first_contribution else goal.start_date

        # Calculate months passed (approximate)
        today = timezone.now().date()
        months_passed = (today.year - start_date.year) * 12 + today.month - start_date.month
        months_passed = max(1, months_passed)  # Avoid division by zero

        # Calculate average monthly
        average_monthly = total_contributions / months_passed

        # Calculate contribution consistency (percentage of months with contributions)
        month_count = {}
        for contrib in contributions:
            key = f"{contrib.date.year}-{contrib.date.month}"
            month_count[key] = month_count.get(key, 0) + 1

        consistency = (len(month_count) / months_passed) * 100 if months_passed > 0 else 0

        # Get contributions by month for progress chart
        progress_by_month = []
        running_total = 0

        # Group contributions by month and calculate running total
        for year in range(start_date.year, today.year + 1):
            for month in range(1, 13):
                # Skip months before start date
                if year == start_date.year and month < start_date.month:
                    continue

                # Skip months after current date
                if year == today.year and month > today.month:
                    continue

                # Get contributions for this month
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

        # Calculate if goal is on track
        is_on_track = goal.is_on_track()

        # Calculate projected completion date based on average monthly contribution
        projected_days = None
        days_behind_schedule = None

        if average_monthly > 0 and goal.target_amount > goal.current_amount:
            amount_remaining = goal.target_amount - goal.current_amount
            months_remaining = amount_remaining / average_monthly
            projected_days = int(months_remaining * 30)  # Approximate

            # Calculate days behind schedule if target date exists
            if goal.target_date:
                days_to_target = (goal.target_date - today).days
                if days_to_target < projected_days:
                    days_behind_schedule = projected_days - days_to_target

        response_data = {
            "goal_id": goal.id,
            "goal_name": goal.name,
            "average_monthly_contribution": str(round(average_monthly, 2)),
            "contribution_consistency": round(consistency, 1),
            "on_track": is_on_track,
            "monthly_contribution_needed": str(goal.monthly_contribution_needed() or 0),
            "progress_by_month": progress_by_month,
        }

        # Add projected completion data if available
        if projected_days is not None:
            projected_date = today + timezone.timedelta(days=projected_days)
            response_data["projected_completion_date"] = projected_date.isoformat()

            if days_behind_schedule is not None:
                response_data["days_behind_schedule"] = days_behind_schedule

        return Response(response_data)

    @action(detail=True, methods=["post"])
    def add_contribution(self, request, pk=None):
        """
        Add a contribution to a goal.
        """
        goal = self.get_object()

        # Create the serializer with goal already set
        serializer = GoalContributionSerializer(data=request.data)
        if serializer.is_valid():
            # Set goal and save
            contribution = serializer.save(goal=goal)

            # Update current amount on the goal
            goal.current_amount += contribution.amount
            goal.save(update_fields=["current_amount"])

            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GoalContributionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing goal contributions.
    """

    serializer_class = GoalContributionSerializer

    def get_queryset(self):
        """
        Return all goal contributions or filter by goal if specified.
        """
        goal_id = self.request.query_params.get("goal", None)
        if goal_id:
            return GoalContribution.objects.filter(goal_id=goal_id)
        return GoalContribution.objects.all()

    def perform_create(self, serializer):
        """
        Save the contribution and update the goal's current amount.
        """
        contribution = serializer.save()

        # Update the goal's current amount
        goal = contribution.goal
        goal.current_amount += contribution.amount
        goal.save(update_fields=["current_amount"])

    def perform_update(self, serializer):
        """
        When updating a contribution, adjust the goal's current amount.
        """
        # Get the old amount
        old_amount = self.get_object().amount

        # Save the updated contribution
        contribution = serializer.save()

        # Update the goal's current amount (subtract old, add new)
        goal = contribution.goal
        goal.current_amount = goal.current_amount - old_amount + contribution.amount
        goal.save(update_fields=["current_amount"])

    def perform_destroy(self, instance):
        """
        When deleting a contribution, reduce the goal's current amount.
        """
        # Get the goal and amount before deletion
        goal = instance.goal
        amount = instance.amount

        # Delete the contribution
        instance.delete()

        # Update the goal's current amount
        goal.current_amount -= amount
        goal.save(update_fields=["current_amount"])
