"""Goals page of the new UI: savings goals and debts, with their quick actions.

The small forms (add to a goal, repay, borrow) answer with a toast. After a change, the
response triggers ``goalsChanged`` (the panel refreshes itself) and, for a milestone or a
paid-off debt, ``celebrate`` (confetti).
"""

from __future__ import annotations

import json
from typing import Any

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views import View

from budgetapp.app.forms import DebtForm, GoalForm
from budgetapp.models import Budget, Debt, DebtTransaction, Goal, GoalContribution
from budgetapp.services.goals import (
    add_repayment,
    debt_view,
    debt_views,
    goal_view,
    goal_views,
    milestone_passed,
    sync_goal_amount,
)
from budgetapp.services.month import build_month_snapshot
from budgetapp.services.quick_add import QuickAddError, parse_amount
from budgetapp.templatetags.app_format import money

from .base import AppTemplateView, month_url, quick_add_context


def panel_context(request: HttpRequest) -> dict[str, Any]:
    """Goals and debts of the user, for the page and its panel."""
    today = timezone.localdate()
    return {
        "goals": goal_views(request.user),
        "debts": debt_views(request.user, today),
        "today": today,
        "month_url": month_url(today),
    }


def toast(
    request: HttpRequest,
    message: str,
    *,
    title: str = "",
    error: bool = False,
    celebrate: bool = False,
) -> HttpResponse:
    """Answer a small form with a toast. A success also refreshes the goals panel."""
    response = render(
        request,
        "app/partials/toast.html",
        {"message": message, "title": title, "error": error},
    )
    if not error:
        events: dict[str, bool] = {"goalsChanged": True}
        if celebrate:
            events["celebrate"] = True
        response["HX-Trigger"] = json.dumps(events)
    return response


class GoalsView(AppTemplateView):
    """Savings goals with progress rings, and debts with payoff dates."""

    template_name = "app/goals.html"
    nav = "goals"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Goals, debts and the two "new" forms."""
        context = super().get_context_data(**kwargs)
        context.update(panel_context(self.request))
        context["goal_form"] = GoalForm(prefix="goal")
        context["debt_form"] = DebtForm(prefix="debt")
        today = context["today"]
        budget = Budget.objects.filter(user=self.request.user, month=today.replace(day=1)).first()
        if budget is not None:
            context["quick_add"] = quick_add_context(budget, build_month_snapshot(budget, today))
        return context


class GoalsPanelView(LoginRequiredMixin, View):
    """HTMX partial: the goals and debts lists, after a change."""

    def get(self, request: HttpRequest) -> HttpResponse:
        """Render the panel."""
        return render(request, "app/partials/goals_panel.html", panel_context(request))


class GoalCreateView(LoginRequiredMixin, View):
    """Start a savings goal (form on the goals page)."""

    def post(self, request: HttpRequest) -> HttpResponse:
        """Save the goal and its starting amount, or return the form with its errors."""
        form = GoalForm(request.POST, prefix="goal")
        if not form.is_valid():
            return render(request, "app/partials/goal_form.html", {"goal_form": form})
        goal = form.save(commit=False)
        goal.user = request.user
        goal.save()
        saved = form.cleaned_data.get("saved")
        if saved:
            GoalContribution.objects.create(goal=goal, amount=saved, source="Starting amount")
            sync_goal_amount(goal)
        response = render(
            request,
            "app/partials/goal_form.html",
            {"goal_form": GoalForm(prefix="goal"), "saved_name": goal.name},
        )
        response["HX-Trigger"] = "goalsChanged"
        return response


class GoalContributeView(LoginRequiredMixin, View):
    """Add money to a goal. Passing 25, 50, 75 or 100 % gets a celebration."""

    def post(self, request: HttpRequest, pk: int) -> HttpResponse:
        """Save the contribution and answer with a toast."""
        goal = get_object_or_404(Goal, pk=pk, user=request.user, is_active=True)
        try:
            amount = parse_amount(request.POST.get("amount", ""))
        except QuickAddError as exc:
            return toast(request, str(exc), error=True)
        sync_goal_amount(goal)
        before = goal_view(goal).pct
        GoalContribution.objects.create(goal=goal, amount=amount, source="monAI app")
        sync_goal_amount(goal)
        after = goal_view(goal)
        milestone = milestone_passed(before, after.pct)
        if milestone == 100:
            return toast(
                request, f"You reached {goal.name}!", title="Goal reached!", celebrate=True
            )
        if milestone:
            return toast(
                request,
                f"{goal.name} is {milestone}% done. {money(after.left)} to go.",
                title=f"{milestone}%!",
                celebrate=True,
            )
        return toast(request, f"Added {money(amount)} to {goal.name}.")


class DebtCreateView(LoginRequiredMixin, View):
    """Add a debt (form on the goals page)."""

    def post(self, request: HttpRequest) -> HttpResponse:
        """Save the debt and what is already borrowed, or return the form with its errors."""
        form = DebtForm(request.POST, prefix="debt")
        if not form.is_valid():
            return render(request, "app/partials/debt_form.html", {"debt_form": form})
        debt = form.save(commit=False)
        debt.user = request.user
        debt.save()
        borrowed = form.cleaned_data.get("borrowed")
        if borrowed:
            DebtTransaction.objects.create(debt=debt, amount=borrowed, notes="Starting amount")
            debt.recalculate_borrowed_amount()
        response = render(
            request,
            "app/partials/debt_form.html",
            {"debt_form": DebtForm(prefix="debt"), "saved_name": debt.name},
        )
        response["HX-Trigger"] = "goalsChanged"
        return response


class DebtRepayView(LoginRequiredMixin, View):
    """Add a repayment to the debt's line in this month's budget."""

    def post(self, request: HttpRequest, pk: int) -> HttpResponse:
        """Save the repayment and answer with a toast; a paid-off debt gets a celebration."""
        debt = get_object_or_404(
            Debt.objects.select_related("debt_tag"), pk=pk, user=request.user, is_active=True
        )
        try:
            amount = parse_amount(request.POST.get("amount", ""))
        except QuickAddError as exc:
            return toast(request, str(exc), error=True)
        today = timezone.localdate()
        budget = Budget.objects.filter(user=request.user, month=today.replace(day=1)).first()
        if budget is None or budget.is_archived:
            return toast(request, "Start this month's budget first.", error=True)
        line = add_repayment(debt, budget, amount)
        view = debt_view(debt, today)
        if view.is_paid_off:
            return toast(request, f"{debt.name} is paid off!", title="Debt free!", celebrate=True)
        return toast(request, f"Added {money(amount)} to the line {line.name} in this month.")


class DebtBorrowView(LoginRequiredMixin, View):
    """Record more money borrowed on a debt, up to its limit."""

    def post(self, request: HttpRequest, pk: int) -> HttpResponse:
        """Save the borrowing and answer with a toast."""
        debt = get_object_or_404(Debt, pk=pk, user=request.user, is_active=True)
        try:
            amount = parse_amount(request.POST.get("amount", ""))
        except QuickAddError as exc:
            return toast(request, str(exc), error=True)
        if debt.borrowed_amount + amount > debt.total_amount:
            room = debt.total_amount - debt.borrowed_amount
            return toast(request, f"You can borrow {money(room)} more at most.", error=True)
        DebtTransaction.objects.create(debt=debt, amount=amount)
        debt.recalculate_borrowed_amount()
        return toast(request, f"Recorded {money(amount)} borrowed for {debt.name}.")
