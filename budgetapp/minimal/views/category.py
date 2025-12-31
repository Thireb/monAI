"""
Category management views.
"""

from django.http import JsonResponse
from django.shortcuts import get_object_or_404

from budgetapp.models import Category

from .base import LoginRequiredTemplateView, LoginRequiredView


class CategoryManagementView(LoginRequiredTemplateView):
    """View for managing categories."""

    template_name = "minimal/category_management.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = Category.objects.filter(user=self.request.user).order_by("name")
        return context


class CategoryListView(LoginRequiredView):
    """View for listing categories via AJAX."""

    def get(self, request, *args, **kwargs):
        category_id = request.GET.get("category_id")

        if category_id:
            # Return specific category for editing
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
            # Return all categories for this user
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

    def post(self, request, *args, **kwargs):
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

    def post(self, request, *args, **kwargs):
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

    def post(self, request, *args, **kwargs):
        category_id = request.POST.get("category_id")

        if not category_id:
            return JsonResponse({"success": False, "error": "Category ID is required"}, status=400)

        try:
            category = get_object_or_404(Category, id=category_id, user=request.user)
            category_name = category.name

            # Count affected expenses for informational message
            affected_expenses = category.expenses.count()

            # Delete the category - Django's on_delete=SET_NULL will automatically
            # set category to null on any expenses using this category
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

