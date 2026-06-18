"""Add per-user Resend API credentials for budget PDF emails."""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0003_alter_customuser_managers"),
    ]

    operations = [
        migrations.AddField(
            model_name="customuser",
            name="resend_api_key",
            field=models.CharField(
                blank=True,
                help_text="Resend API key for sending budget PDF emails from this account.",
                max_length=255,
            ),
        ),
        migrations.AddField(
            model_name="customuser",
            name="resend_from_email",
            field=models.EmailField(
                blank=True,
                help_text="Verified sender address in your Resend account.",
                max_length=254,
            ),
        ),
    ]
