# Generated manually for ScriptExecution model

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    """
    Add ScriptExecution model for tracking management script runs.
    """

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("budgetapp", "0017_remove_expense_tag"),
    ]

    operations = [
        migrations.CreateModel(
            name="ScriptExecution",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("script_name", models.CharField(db_index=True, max_length=100)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("started", "Started"),
                            ("success", "Success"),
                            ("failed", "Failed"),
                        ],
                        default="started",
                        max_length=20,
                    ),
                ),
                ("started_at", models.DateTimeField(auto_now_add=True)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
                ("duration_seconds", models.FloatField(blank=True, null=True)),
                ("output", models.TextField(blank=True)),
                ("error_message", models.TextField(blank=True)),
                ("arguments", models.JSONField(blank=True, default=dict)),
                (
                    "executed_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="script_executions",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Script Execution",
                "verbose_name_plural": "Script Executions",
                "ordering": ["-started_at"],
            },
        ),
        migrations.AddIndex(
            model_name="scriptexecution",
            index=models.Index(
                fields=["script_name", "-started_at"],
                name="budgetapp_s_script__abc123_idx",
            ),
        ),
    ]

