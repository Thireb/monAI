"""Category management views."""

from __future__ import annotations

from typing import Any

from django.http import HttpRequest, JsonResponse
from django.shortcuts import get_object_or_404

from budgetapp.models import Category

from .base import LoginRequiredTemplateView, LoginRequiredView


class CategoryManagementView(LoginRequiredTemplateView):
    """View for managing categories."""

    template_name = "minimal/category_management.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Return categories ordered by name for the management page."""
        context = super().get_context_data(**kwargs)
        context["categories"] = Category.objects.filter(user=self.request.user).order_by("name")
        return context


class CategoryListView(LoginRequiredView):
    """View for listing categories via AJAX."""

    def get(
        self,
        request: HttpRequest,
        *args: Any,
        **kwargs: Any,
    ) -> JsonResponse:
        """Return one category or all categories as JSON."""
        category_id = request.GET.get("category_id")

        if category_id:
            try:
                category = Category.objects.get(id=category_id, user=request.user)
                return JsonResponse(
                    {
                        "success": True,
                        "category": {
                            "id": category.id,
                            "name": category.name,
                            "description": category.description,
                            "color": category.color,
                        },
                    }
                )
            except Category.DoesNotExist:
                return JsonResponse({"success": False, "error": "Category not found"}, status=404)
        else:
            categories = Category.objects.filter(user=request.user).order_by("name")
            return JsonResponse(
                {
                    "success": True,
                    "categories": [
                        {
                            "id": category.id,
                            "name": category.name,
                            "description": category.description,
                            "color": category.color,
                        }
                        for category in categories
                    ],
                }
            )


class CategoryCreateView(LoginRequiredView):
    """View for creating new categories via AJAX."""

    def post(
        self,
        request: HttpRequest,
        *args: Any,
        **kwargs: Any,
    ) -> JsonResponse:
        """Create a category from POST data and return JSON."""
        name = request.POST.get("name")
        description = request.POST.get("description", "")
        color = request.POST.get("color", "#2196f3")

        if not name:
            return JsonResponse(
                {"success": False, "error": "Category name is required"}, status=400
            )

        try:
            category = Category.objects.create(
                user=request.user, name=name, description=description, color=color
            )
            return JsonResponse(
                {
                    "success": True,
                    "message": f'Category "{name}" created successfully!',
                    "category": {
                        "id": category.id,
                        "name": category.name,
                        "description": category.description,
                        "color": category.color,
                    },
                }
            )
        except Exception as e:
            return JsonResponse(
                {"success": False, "error": f"Error creating category: {str(e)}"}, status=400
            )


class CategoryUpdateView(LoginRequiredView):
    """View for updating categories via AJAX."""

    def post(
        self,
        request: HttpRequest,
        *args: Any,
        **kwargs: Any,
    ) -> JsonResponse:
        """Update a category from POST data and return JSON."""
        category_id = request.POST.get("category_id")
        name = request.POST.get("name")
        description = request.POST.get("description", "")
        color = request.POST.get("color", "#2196f3")

        if not category_id or not name:
            return JsonResponse(
                {"success": False, "error": "Category ID and name are required"}, status=400
            )

        try:
            category = get_object_or_404(Category, id=category_id, user=request.user)
            category.name = name
            category.description = description
            category.color = color
            category.save()

            return JsonResponse(
                {
                    "success": True,
                    "message": f'Category "{name}" updated successfully!',
                    "category": {
                        "id": category.id,
                        "name": category.name,
                        "description": category.description,
                        "color": category.color,
                    },
                }
            )
        except Exception as e:
            return JsonResponse(
                {"success": False, "error": f"Error updating category: {str(e)}"}, status=400
            )


class CategoryDeleteView(LoginRequiredView):
    """View for deleting categories via AJAX."""

    def post(
        self,
        request: HttpRequest,
        *args: Any,
        **kwargs: Any,
    ) -> JsonResponse:
        """Delete a category and report affected expenses."""
        category_id = request.POST.get("category_id")

        if not category_id:
            return JsonResponse({"success": False, "error": "Category ID is required"}, status=400)

        try:
            category = get_object_or_404(Category, id=category_id, user=request.user)
            category_name = category.name

            affected_expenses = category.expenses.count()

            category.delete()

            message = f'Category "{category_name}" deleted successfully!'
            if affected_expenses > 0:
                message += f" ({affected_expenses} expense(s) updated to uncategorized)"

            return JsonResponse(
                {
                    "success": True,
                    "message": message,
                    "category_id": category_id,
                }
            )
        except Exception as e:
            return JsonResponse(
                {"success": False, "error": f"Error deleting category: {str(e)}"}, status=400
            )
