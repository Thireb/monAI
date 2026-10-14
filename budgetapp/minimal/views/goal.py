"""Savings goal views for the minimal UI."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from django.http import HttpRequest, JsonResponse
from django.shortcuts import get_object_or_404

from budgetapp.forms import GoalContributionForm, GoalForm
from budgetapp.models import Category, Goal, GoalContribution
from budgetapp.services.goals import sync_goal_amount

from .base import LoginRequiredTemplateView, LoginRequiredView


def _sync_goal_current_amount(goal: Goal) -> None:
    """Align stored current_amount with sum of contributions.

    Args:
        goal: The goal to synchronize.
    """
    sync_goal_amount(goal)


class GoalListView(LoginRequiredTemplateView):
    """List active and completed savings goals."""

    template_name = "minimal/goals/goal_list.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Return active and completed goals with create form."""
        context = super().get_context_data(**kwargs)
        user = self.request.user
        all_goals = Goal.objects.filter(user=user).select_related("category")
        active_goals = []
        completed_goals = []
        for goal in all_goals.order_by("-start_date"):
            _sync_goal_current_amount(goal)
            goal.remaining_to_save = max(Decimal("0"), goal.target_amount - goal.current_amount)
            is_complete = goal.current_amount >= goal.target_amount
            if goal.is_active and not is_complete:
                active_goals.append(goal)
            else:
                completed_goals.append(goal)
        create_form = GoalForm(user=user)
        context.update(
            {
                "active_goals": active_goals,
                "completed_goals": completed_goals,
                "goal_create_form": create_form,
                "category_options": Category.objects.filter(user=user),
            }
        )
        return context


class GoalDetailView(LoginRequiredTemplateView):
    """Goal detail with contributions."""

    template_name = "minimal/goals/goal_detail.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Return goal detail with contributions and edit forms."""
        context = super().get_context_data(**kwargs)
        goal_id = self.kwargs.get("goal_id")
        goal = get_object_or_404(
            Goal.objects.select_related("category"), id=goal_id, user=self.request.user
        )
        _sync_goal_current_amount(goal)
        goal.remaining_to_save = max(Decimal("0"), goal.target_amount - goal.current_amount)
        contributions = goal.contributions.all().order_by("-date", "-id")
        contribution_form = GoalContributionForm()
        edit_form = GoalForm(instance=goal, user=self.request.user)
        track_status = goal.is_on_track()
        context.update(
            {
                "goal": goal,
                "contributions": contributions,
                "contribution_form": contribution_form,
                "goal_edit_form": edit_form,
                "monthly_needed": goal.monthly_contribution_needed(),
                "on_track": track_status,
                "remaining_to_save": max(Decimal("0"), goal.target_amount - goal.current_amount),
                "category_options": Category.objects.filter(user=self.request.user),
            }
        )
        return context


class GoalCreateView(LoginRequiredView):
    """Create a goal via POST (AJAX or form)."""

    def post(
        self,
        request: HttpRequest,
        *args: Any,
        **kwargs: Any,
    ) -> JsonResponse:
        """Create a savings goal from POST data."""
        form = GoalForm(request.POST, user=request.user)
        if not form.is_valid():
            errors = [f"{k}: {v[0]}" for k, v in form.errors.items()]
            return JsonResponse(
                {"success": False, "error": "; ".join(errors) if errors else "Invalid data"},
                status=400,
            )

        goal = form.save(commit=False)
        goal.user = request.user
        goal.save()

        cat_name = goal.category.name if goal.category else ""

        return JsonResponse(
            {
                "success": True,
                "message": "Goal created successfully.",
                "goal": {
                    "id": goal.id,
                    "name": goal.name,
                    "description": goal.description or "",
                    "target_amount": str(goal.target_amount),
                    "current_amount": str(goal.current_amount),
                    "remaining_to_save": str(
                        max(Decimal("0"), goal.target_amount - goal.current_amount)
                    ),
                    "progress_percentage": goal.progress_percentage,
                    "category_name": cat_name,
                    "is_active": goal.is_active,
                },
            }
        )


class GoalUpdateView(LoginRequiredView):
    """Update a goal via POST."""

    def post(
        self,
        request: HttpRequest,
        *args: Any,
        **kwargs: Any,
    ) -> JsonResponse:
        """Update a savings goal from POST data."""
        goal_id = request.POST.get("goal_id")
        if not goal_id:
            return JsonResponse({"success": False, "error": "Goal ID is required"}, status=400)

        goal = get_object_or_404(Goal, id=goal_id, user=request.user)
        form = GoalForm(request.POST, instance=goal, user=request.user)
        if not form.is_valid():
            errors = [f"{k}: {v[0]}" for k, v in form.errors.items()]
            return JsonResponse(
                {"success": False, "error": "; ".join(errors) if errors else "Invalid data"},
                status=400,
            )

        goal = form.save()
        cat_name = goal.category.name if goal.category else ""

        return JsonResponse(
            {
                "success": True,
                "message": "Goal updated successfully.",
                "goal": {
                    "id": goal.id,
                    "name": goal.name,
                    "description": goal.description or "",
                    "target_amount": str(goal.target_amount),
                    "current_amount": str(goal.current_amount),
                    "remaining_to_save": str(
                        max(Decimal("0"), goal.target_amount - goal.current_amount)
                    ),
                    "progress_percentage": goal.progress_percentage,
                    "category_name": cat_name,
                    "is_active": goal.is_active,
                    "start_date": goal.start_date.isoformat(),
                    "target_date": goal.target_date.isoformat() if goal.target_date else "",
                },
            }
        )


class GoalDeleteView(LoginRequiredView):
    """Delete a goal."""

    def post(
        self,
        request: HttpRequest,
        *args: Any,
        **kwargs: Any,
    ) -> JsonResponse:
        """Delete a savings goal."""
        goal_id = request.POST.get("goal_id")
        if not goal_id:
            return JsonResponse({"success": False, "error": "Goal ID is required"}, status=400)

        goal = get_object_or_404(Goal, id=goal_id, user=request.user)
        name = goal.name
        goal.delete()

        return JsonResponse(
            {"success": True, "message": "Goal deleted.", "goal_id": goal_id, "name": name}
        )


class GoalContributionCreateView(LoginRequiredView):
    """Add a contribution to a goal."""

    def post(
        self,
        request: HttpRequest,
        *args: Any,
        **kwargs: Any,
    ) -> JsonResponse:
        """Create a contribution for the given goal."""
        goal_id = request.POST.get("goal_id")
        if not goal_id:
            return JsonResponse({"success": False, "error": "Goal ID is required"}, status=400)

        goal = get_object_or_404(Goal, id=goal_id, user=request.user)
        form = GoalContributionForm(request.POST)
        if not form.is_valid():
            errors = [f"{k}: {v[0]}" for k, v in form.errors.items()]
            return JsonResponse(
                {"success": False, "error": "; ".join(errors) if errors else "Invalid data"},
                status=400,
            )

        contribution = form.save(commit=False)
        contribution.goal = goal
        contribution.save()

        _sync_goal_current_amount(goal)
        goal.refresh_from_db()

        return JsonResponse(
            {
                "success": True,
                "message": "Contribution added.",
                "contribution": {
                    "id": contribution.id,
                    "amount": str(contribution.amount),
                    "date": contribution.date.isoformat(),
                    "source": contribution.source or "",
                    "notes": contribution.notes or "",
                },
                "goal": {
                    "id": goal.id,
                    "current_amount": str(goal.current_amount),
                    "progress_percentage": goal.progress_percentage,
                },
            }
        )


class GoalContributionUpdateView(LoginRequiredView):
    """Update a contribution."""

    def post(
        self,
        request: HttpRequest,
        *args: Any,
        **kwargs: Any,
    ) -> JsonResponse:
        """Update an existing goal contribution."""
        cid = request.POST.get("contribution_id")
        goal_id = request.POST.get("goal_id")
        if not cid or not goal_id:
            return JsonResponse(
                {"success": False, "error": "Contribution and goal IDs are required"},
                status=400,
            )

        contribution = get_object_or_404(
            GoalContribution,
            id=cid,
            goal_id=goal_id,
            goal__user=request.user,
        )
        form = GoalContributionForm(request.POST, instance=contribution)
        if not form.is_valid():
            errors = [f"{k}: {v[0]}" for k, v in form.errors.items()]
            return JsonResponse(
                {"success": False, "error": "; ".join(errors) if errors else "Invalid data"},
                status=400,
            )

        contribution = form.save()
        goal = contribution.goal
        _sync_goal_current_amount(goal)
        goal.refresh_from_db()

        return JsonResponse(
            {
                "success": True,
                "message": "Contribution updated.",
                "contribution": {
                    "id": contribution.id,
                    "amount": str(contribution.amount),
                    "date": contribution.date.isoformat(),
                    "source": contribution.source or "",
                    "notes": contribution.notes or "",
                },
                "goal": {
                    "id": goal.id,
                    "current_amount": str(goal.current_amount),
                    "progress_percentage": goal.progress_percentage,
                },
            }
        )


class GoalContributionDeleteView(LoginRequiredView):
    """Delete a contribution."""

    def post(
        self,
        request: HttpRequest,
        *args: Any,
        **kwargs: Any,
    ) -> JsonResponse:
        """Delete a goal contribution."""
        cid = request.POST.get("contribution_id")
        if not cid:
            return JsonResponse(
                {"success": False, "error": "Contribution ID is required"},
                status=400,
            )

        contribution = get_object_or_404(
            GoalContribution,
            id=cid,
            goal__user=request.user,
        )
        goal = contribution.goal
        contribution.delete()

        _sync_goal_current_amount(goal)
        goal.refresh_from_db()

        return JsonResponse(
            {
                "success": True,
                "message": "Contribution removed.",
                "goal": {
                    "id": goal.id,
                    "current_amount": str(goal.current_amount),
                    "progress_percentage": goal.progress_percentage,
                },
            }
        )
