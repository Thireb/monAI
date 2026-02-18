from django.contrib import admin

from .models import ScriptExecution


@admin.register(ScriptExecution)
class ScriptExecutionAdmin(admin.ModelAdmin):
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

    def has_add_permission(self, request):
        """Prevent manual creation - only created by script commands."""
        return False

    def has_change_permission(self, request, obj=None):
        """Prevent editing execution records."""
        return False
