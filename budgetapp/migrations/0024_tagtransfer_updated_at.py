from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("budgetapp", "0023_tagtransfer"),
    ]

    operations = [
        migrations.AddField(
            model_name="tagtransfer",
            name="updated_at",
            field=models.DateTimeField(auto_now=True),
        ),
    ]
