from django.apps import AppConfig


class BudgetappConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "budgetapp"

    def ready(self):
        import budgetapp.signals  # noqa: F401
