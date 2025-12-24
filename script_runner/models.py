"""
Models for the script_runner app.

Tracks script execution history and script registry.
"""

from django.conf import settings
from django.db import models
from django.utils import timezone


class ScriptExecution(models.Model):
    """
    Tracks execution history of management scripts.

    This model logs when each script was run, by whom, and whether it succeeded.
    """

    class Status(models.TextChoices):
        STARTED = "started", "Started"
        SUCCESS = "success", "Success"
        FAILED = "failed", "Failed"
        SKIPPED = "skipped", "Skipped"

    script_name = models.CharField(max_length=100, db_index=True)
    code_version = models.CharField(max_length=20, blank=True, db_index=True)
    executed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="script_executions",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.STARTED,
    )
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.FloatField(null=True, blank=True)
    output = models.TextField(blank=True)
    error_message = models.TextField(blank=True)
    arguments = models.JSONField(default=dict, blank=True)
    batch_id = models.CharField(max_length=50, blank=True, db_index=True)

    class Meta:
        ordering = ["-started_at"]
        verbose_name = "Script Execution"
        verbose_name_plural = "Script Executions"
        indexes = [
            models.Index(fields=["script_name", "-started_at"]),
            models.Index(fields=["code_version", "-started_at"]),
        ]

    def __str__(self):
        return f"{self.script_name} - {self.status} at {self.started_at}"

    def mark_success(self, output=""):
        """Mark the script execution as successful."""
        self.status = self.Status.SUCCESS
        self.completed_at = timezone.now()
        self.duration_seconds = (self.completed_at - self.started_at).total_seconds()
        self.output = output
        self.save()

    def mark_failed(self, error_message):
        """Mark the script execution as failed."""
        self.status = self.Status.FAILED
        self.completed_at = timezone.now()
        self.duration_seconds = (self.completed_at - self.started_at).total_seconds()
        self.error_message = error_message
        self.save()

    def mark_skipped(self, reason=""):
        """Mark the script execution as skipped."""
        self.status = self.Status.SKIPPED
        self.completed_at = timezone.now()
        self.duration_seconds = 0
        self.output = reason
        self.save()
