from django.core.management.base import BaseCommand
from budgetapp.models import Category

class Command(BaseCommand):
    help = 'Creates default expense categories'

    def handle(self, *args, **kwargs):
        default_categories = [
            {
                'name': 'Housing',
                'icon': 'fa-home',
                'color': '#FF6B6B',
                'description': 'Rent, mortgage, maintenance, and housing expenses'
            },
            {
                'name': 'Transportation',
                'icon': 'fa-car',
                'color': '#4ECDC4',
                'description': 'Car payments, fuel, public transit, and maintenance'
            },
            {
                'name': 'Food & Dining',
                'icon': 'fa-utensils',
                'color': '#45B7D1',
                'description': 'Groceries, restaurants, and food delivery'
            },
            {
                'name': 'Utilities',
                'icon': 'fa-bolt',
                'color': '#96CEB4',
                'description': 'Electricity, water, gas, internet, and phone'
            },
            {
                'name': 'Healthcare',
                'icon': 'fa-hospital',
                'color': '#D4A5A5',
                'description': 'Medical expenses, medications, and insurance'
            },
            {
                'name': 'Entertainment',
                'icon': 'fa-film',
                'color': '#9B59B6',
                'description': 'Movies, games, streaming services, and hobbies'
            },
            {
                'name': 'Shopping',
                'icon': 'fa-shopping-bag',
                'color': '#E74C3C',
                'description': 'Clothing, electronics, and personal items'
            },
            {
                'name': 'Education',
                'icon': 'fa-graduation-cap',
                'color': '#3498DB',
                'description': 'Tuition, books, courses, and training'
            },
            {
                'name': 'Savings',
                'icon': 'fa-piggy-bank',
                'color': '#2ECC71',
                'description': 'Emergency fund, investments, and long-term savings'
            },
            {
                'name': 'Miscellaneous',
                'icon': 'fa-ellipsis-h',
                'color': '#95A5A6',
                'description': 'Other uncategorized expenses'
            }
        ]

        for category_data in default_categories:
            Category.objects.get_or_create(
                name=category_data['name'],
                defaults={
                    'icon': category_data['icon'],
                    'color': category_data['color'],
                    'description': category_data['description']
                }
            )
            self.stdout.write(
                self.style.SUCCESS(f'Successfully created category "{category_data["name"]}"')
            ) 