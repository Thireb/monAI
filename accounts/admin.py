"""Django admin registration for user accounts."""

from __future__ import annotations

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """Admin configuration for the CustomUser model."""

    model = CustomUser
    list_display = (
        "email",
        "username",
        "is_staff",
        "is_active",
        "date_joined",
    )
    list_filter = (
        "is_staff",
        "is_superuser",
        "is_active",
    )
    search_fields = ("email", "username")
    ordering = ("-date_joined",)

    fieldsets = (
        (None, {"fields": ("email", "username", "password")}),
        (
            "Personal Info",
            {"fields": ("first_name", "last_name", "resend_from_email")},
        ),
        (
            "Resend (budget PDF)",
            {
                "fields": ("resend_api_key",),
                "classes": ("collapse",),
                "description": "Per-user Resend credentials for budget PDF emails.",
            },
        ),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        (
            "Important dates",
            {"fields": ("last_login", "date_joined")},
        ),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "username",
                    "password1",
                    "password2",
                    "is_staff",
                    "is_active",
                ),
            },
        ),
    )
