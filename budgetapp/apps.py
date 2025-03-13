from django.apps import AppConfig


class BudgetappConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "budgetapp"

    def ready(self):
        # Import tasks but don't execute them during app initialization
        from .tasks import setup_periodic_tasks
