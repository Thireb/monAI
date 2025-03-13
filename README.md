# Django Budget Tracker

A personal budget tracking application built with Django. This app helps you manage your monthly expenses, track spending by categories, and maintain a clear view of your financial health.

## Features

- Monthly budget management
- Expense categorization
- Expense breakdown support
- Income tracking with history
- Category-wise expense statistics
- Archive functionality for old budgets
- Recurring expense support
- Modern Material Design UI

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- virtualenv (recommended)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/django_budget_tracker.git
cd django_budget_tracker
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```

3. Install required packages:
```bash
pip install -r requirements.txt
```

4. Apply database migrations:
```bash
python manage.py migrate
```

5. Create a superuser (admin):
```bash
python manage.py createsuperuser
```

6. Run the development server:
```bash
python manage.py runserver
```

The application will be available at `http://127.0.0.1:8000/`

## Code Formatting with Pre-commit

This project uses [pre-commit](https://pre-commit.com/) hooks to automatically format and check code before committing. This ensures consistent code style and quality across the project.

### Setup

1. Install pre-commit:
   ```bash
   pip install pre-commit
   ```

2. Install the git hooks:
   ```bash
   pre-commit install
   ```

### Usage

Pre-commit will automatically run on `git commit`. If any checks fail, the commit will be aborted and the issues will be fixed or reported. After the issues are fixed, you can add the changes and try committing again.

To manually run pre-commit on all files:
```bash
pre-commit run --all-files
```

### Features

The pre-commit configuration includes:
- Python formatting with Black
- Import sorting with isort
- Python code quality with flake8
- Django HTML template formatting with djLint
- JavaScript and CSS formatting with prettier
- Trailing whitespace and end-of-file fixing
- Security checking with bandit

## Usage

1. Log in with your superuser credentials
2. Create categories for your expenses (e.g., Groceries, Rent, Utilities)
3. Create a new budget for the current month
4. Add your monthly income
5. Start tracking expenses by category

## Project Structure

```
django_budget_tracker/
├── budgetapp/              # Main application directory
│   ├── migrations/         # Database migrations
│   ├── templates/         # HTML templates
│   │   └── material/     # Material design templates
│   ├── models.py         # Database models
│   ├── views.py          # View logic
│   ├── forms.py          # Form definitions
│   └── urls.py           # URL configurations
├── static/               # Static files (CSS, JS, images)
├── manage.py            # Django management script
└── requirements.txt     # Project dependencies
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Built with Django web framework
- Uses Material Design for the UI
- Inspired by the need for a simple, focused budget tracking solution
