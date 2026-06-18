"""Tag management views."""

from __future__ import annotations

from typing import Any

from django.http import HttpRequest, JsonResponse
from django.shortcuts import get_object_or_404

from budgetapp.models import Tag

from .base import LoginRequiredTemplateView, LoginRequiredView


class TagManagementView(LoginRequiredTemplateView):
    """View for managing tags."""

    template_name = "minimal/tag_management.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Return tags ordered by name for the management page."""
        context = super().get_context_data(**kwargs)
        context["tags"] = Tag.objects.filter(user=self.request.user).order_by("name")
        return context


class TagCreateView(LoginRequiredView):
    """View for creating new tags via AJAX."""

    def post(
        self,
        request: HttpRequest,
        *args: Any,
        **kwargs: Any,
    ) -> JsonResponse:
        """Create a tag from POST data and return JSON."""
        name = request.POST.get("name")
        description = request.POST.get("description", "")
        color = request.POST.get("color", "#2196f3")

        if not name:
            return JsonResponse({"status": "error", "message": "Tag name is required"}, status=400)

        try:
            tag = Tag.objects.create(
                user=request.user, name=name, description=description, color=color
            )
            return JsonResponse(
                {
                    "status": "success",
                    "message": f'Tag "{name}" created successfully!',
                    "tag": {
                        "id": tag.id,
                        "name": tag.name,
                        "description": tag.description,
                        "color": tag.color,
                        "created_at": tag.created_at.strftime("%Y-%m-%d %H:%M"),
                    },
                }
            )
        except Exception as e:
            return JsonResponse(
                {"status": "error", "message": f"Error creating tag: {str(e)}"}, status=400
            )


class TagUpdateView(LoginRequiredView):
    """View for updating tags via AJAX."""

    def post(
        self,
        request: HttpRequest,
        *args: Any,
        **kwargs: Any,
    ) -> JsonResponse:
        """Update a tag from POST data and return JSON."""
        tag_id = request.POST.get("tag_id")
        name = request.POST.get("name")
        description = request.POST.get("description", "")
        color = request.POST.get("color", "#2196f3")

        if not tag_id or not name:
            return JsonResponse(
                {"status": "error", "message": "Tag ID and name are required"}, status=400
            )

        try:
            tag = get_object_or_404(Tag, id=tag_id, user=request.user)
            tag.name = name
            tag.description = description
            tag.color = color
            tag.save()

            return JsonResponse(
                {
                    "status": "success",
                    "message": f'Tag "{name}" updated successfully!',
                    "tag": {
                        "id": tag.id,
                        "name": tag.name,
                        "description": tag.description,
                        "color": tag.color,
                        "updated_at": tag.updated_at.strftime("%Y-%m-%d %H:%M"),
                    },
                }
            )
        except Exception as e:
            return JsonResponse(
                {"status": "error", "message": f"Error updating tag: {str(e)}"}, status=400
            )


class TagDeleteView(LoginRequiredView):
    """View for deleting tags via AJAX."""

    def post(
        self,
        request: HttpRequest,
        *args: Any,
        **kwargs: Any,
    ) -> JsonResponse:
        """Delete a tag and cascade cleanup associated debts."""
        tag_id = request.POST.get("tag_id")

        if not tag_id:
            return JsonResponse({"status": "error", "message": "Tag ID is required"}, status=400)

        try:
            tag = get_object_or_404(Tag, id=tag_id, user=request.user)
            tag_name = tag.name

            affected_expenses = tag.expenses.count()

            associated_debts = tag.debts.all()
            deleted_debts_count = 0
            deleted_transactions_count = 0
            if associated_debts.exists():
                for debt in associated_debts:
                    deleted_transactions_count += debt.transactions.count()
                deleted_debts_count = associated_debts.count()
                associated_debts.delete()

            tag.delete()

            message = f'Tag "{tag_name}" deleted successfully!'
            if deleted_debts_count > 0:
                message += f" ({deleted_debts_count} debt(s)"
                if deleted_transactions_count > 0:
                    message += f" and {deleted_transactions_count} transaction(s)"
                message += " removed)"
            elif affected_expenses > 0:
                message += f" ({affected_expenses} expense(s) updated to no tag)"

            return JsonResponse(
                {
                    "status": "success",
                    "message": message,
                    "tag_id": tag_id,
                }
            )
        except Exception as e:
            return JsonResponse(
                {"status": "error", "message": f"Error deleting tag: {str(e)}"}, status=400
            )
