import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("budgetapp", "0022_bill_reminder_and_expense_link"),
    ]

    operations = [
        migrations.CreateModel(
            name="TagTransfer",
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
                (
                    "amount",
                    models.DecimalField(
                        decimal_places=2, max_digits=10
                    ),
                ),
                (
                    "date",
                    models.DateField(default=django.utils.timezone.now),
                ),
                (
                    "note",
                    models.CharField(blank=True, max_length=255),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "budget",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="tag_transfers",
                        to="budgetapp.budget",
                    ),
                ),
                (
                    "from_tag",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="transfers_out",
                        to="budgetapp.tag",
                    ),
                ),
                (
                    "to_tag",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="transfers_in",
                        to="budgetapp.tag",
                    ),
                ),
            ],
            options={
                "verbose_name_plural": "Tag transfers",
                "ordering": ["-created_at"],
            },
        ),
    ]
