# Generated manually for removing redundant tag CharField

from django.db import migrations


class Migration(migrations.Migration):
    """
    Remove the redundant Expense.tag CharField.

    The tag functionality is now handled entirely by the tag_foreign_key
    ForeignKey field pointing to the Tag model.
    """

    dependencies = [
        ("budgetapp", "0016_assign_data_to_user"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="expense",
            name="tag",
        ),
    ]

