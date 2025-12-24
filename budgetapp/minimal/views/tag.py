"""
Tag management views.
"""

from django.http import JsonResponse
from django.shortcuts import get_object_or_404

from budgetapp.models import Tag

from .base import LoginRequiredTemplateView, LoginRequiredView


class TagManagementView(LoginRequiredTemplateView):
    """View for managing tags."""

    template_name = "minimal/tag_management.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["tags"] = Tag.objects.filter(user=self.request.user).order_by("name")
        return context


class TagCreateView(LoginRequiredView):
    """View for creating new tags via AJAX."""

    def post(self, request, *args, **kwargs):
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

    def post(self, request, *args, **kwargs):
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

    def post(self, request, *args, **kwargs):
        tag_id = request.POST.get("tag_id")

        if not tag_id:
            return JsonResponse({"status": "error", "message": "Tag ID is required"}, status=400)

        try:
            tag = get_object_or_404(Tag, id=tag_id, user=request.user)
            tag_name = tag.name
            tag.delete()

            return JsonResponse(
                {
                    "status": "success",
                    "message": f'Tag "{tag_name}" deleted successfully!',
                    "tag_id": tag_id,
                }
            )
        except Exception as e:
            return JsonResponse(
                {"status": "error", "message": f"Error deleting tag: {str(e)}"}, status=400
            )

