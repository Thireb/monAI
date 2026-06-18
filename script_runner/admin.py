"""Django admin configuration for script_runner models."""
from __future__ import annotations

from django.contrib import admin
from django.http import HttpRequest

from .models import ScriptExecution


@admin.register(ScriptExecution)
class ScriptExecutionAdmin(admin.ModelAdmin):
    """Read-only admin for script execution audit records."""

    list_display = (
        "script_name",
        "status",
        "code_version",
        "started_at",
        "duration_seconds",
        "batch_id",
    )
    list_filter = ("status", "script_name", "code_version", "started_at")
    search_fields = ("script_name", "output", "error_message", "batch_id")
    date_hierarchy = "started_at"
    readonly_fields = (
        "script_name",
        "code_version",
        "status",
        "started_at",
        "completed_at",
        "duration_seconds",
        "output",
        "error_message",
        "arguments",
        "executed_by",
        "batch_id",
    )

    def has_add_permission(self, request: HttpRequest) -> bool:
        """Prevent manual creation; records are created by script commands only."""
        return False

    def has_change_permission(
        self, request: HttpRequest, obj: ScriptExecution | None = None
    ) -> bool:
        """Prevent editing execution records."""
        return False
