# monAI Budget Tracker - Documentation

> **Single Source of Truth** for the monAI Budget Tracker application.

**Version:** 1.0.0  
**Last Updated:** December 2024

---

## Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Configuration](#configuration)
4. [Project Structure](#project-structure)
5. [Core Features](#core-features)
6. [Script Runner](#script-runner)
7. [API Reference](#api-reference)
8. [Android APK Building](#android-apk-building)
9. [Development Guidelines](#development-guidelines)
10. [Database Schema](#database-schema)
11. [Deployment](#deployment)

---

## Overview

monAI is a personal budget tracking application built with Django. It features:

- **Budget Management** - Create monthly budgets with income and expense tracking
- **Expense Tracking** - Categorize expenses with tags, sub-expenses, and recurring markers
- **Debt Tracking** - Track borrowings and repayments
- **Goal Setting** - Set and track financial goals
- **Android App** - Capacitor-based Android wrapper
- **Script Runner** - Centralized script management with version tracking

### Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | Django 5.1, Python 3.13 |
| Database | SQLite (development), PostgreSQL (production) |
| Frontend | Django Templates, Alpine.js, Anime.js, Bootstrap 5 |
| Mobile | Capacitor (Android) |
| Task Queue | Celery + Redis |
| Authentication | Django Allauth |

---

## Quick Start

### Prerequisites

- Python 3.11+
- pyenv (recommended)
- Redis (for Celery)
- Android SDK (for APK building)

### Setup

```bash
# Clone and enter directory
cd django_budget_tracker

# Create virtual environment
pyenv virtualenv 3.13.1 budget_tracker_env
pyenv activate budget_tracker_env

# Install dependencies
pip install -r requirements.txt

# Copy and edit configuration
cp config.yaml.example config.yaml
# Edit config.yaml with your settings

# Run migrations
python manage.py migrate

# Create superuser
python manage.py setup_superuser

# Run development server
python manage.py runserver
```

---

## Configuration

All configuration is centralized in `config.yaml`:

```yaml
# Application Settings
app:
  name: "monAI"
  version: "1.0.0"      # Used by run_scripts for version matching
  debug: true
  secret_key: "your-secret-key-here"

# Server Settings
server:
  allowed_hosts:
    - "localhost"
    - "127.0.0.1"
    - "*.ngrok-free.app"
  timezone: "Asia/Karachi"

# URLs for APK Building
urls:
  local: "http://192.168.1.100:8000"
  ngrok: "https://your-subdomain.ngrok-free.app"

# Database Settings
database:
  engine: "sqlite3"
  name: "db.sqlite3"

# Celery Settings
celery:
  broker_url: "redis://localhost:6379/0"
  result_backend: "redis://localhost:6379/0"

# Email Settings
email:
  backend: "console"  # "console" or "smtp"

# Initial Superuser (for setup_superuser command)
superuser:
  email: ""
  username: ""
  password: ""
```

### Environment-Specific Settings

| Setting | Development | Production |
|---------|-------------|------------|
| `app.debug` | `true` | `false` |
| `app.secret_key` | Any string | 50+ char random string |
| `email.backend` | `console` | `smtp` |
| `database.engine` | `sqlite3` | `postgresql` |

---

## Project Structure

```
django_budget_tracker/
├── accounts/                 # Custom user model and auth
│   ├── models.py            # CustomUser model
│   ├── views.py             # Profile views
│   └── management/commands/
│       └── setup_superuser.py
│
├── budgetapp/               # Main application
│   ├── models.py            # Budget, Expense, Goal, Debt models
│   ├── minimal/             # Minimal theme views
│   │   └── views/           # Modular view package
│   │       ├── base.py      # Base view classes
│   │       ├── home.py      # Home & calendar
│   │       ├── budget.py    # Budget CRUD
│   │       ├── expense.py   # Expense CRUD
│   │       ├── subexpense.py
│   │       ├── category.py  # Category management
│   │       ├── tag.py       # Tag management
│   │       ├── debt.py      # Debt management
│   │       └── stats.py     # Statistics views
│   ├── api.py               # Budget API viewset
│   ├── api_goals.py         # Goals API viewset
│   └── management/commands/
│       ├── backup_data.py
│       ├── restore_data.py
│       ├── build_apk.py
│       ├── create_default_categories.py
│       └── ...
│
├── script_runner/           # Script management app
│   ├── models.py            # ScriptExecution model
│   ├── registry.py          # Script registry
│   └── management/commands/
│       ├── run_scripts.py   # Run all version scripts
│       └── list_scripts.py  # List available scripts
│
├── budget_tracker/          # Django project settings
│   ├── settings.py
│   ├── config.py            # Config loader
│   └── urls.py
│
├── capacitor-app/           # Android app wrapper
│   ├── www/index.html
│   ├── android/
│   └── package.json
│
├── scripts/                 # Build scripts
│   └── build_apks.py        # APK builder
│
├── config.yaml              # Main configuration file
└── requirements.txt
```

---

## Core Features

### Budget Management

Each budget represents a monthly financial plan:

```python
# Create a budget
budget = Budget.objects.create(
    user=user,
    month=date(2024, 12, 1),
    income=Decimal("5000.00"),
    currency="PKR"
)

# Get remaining budget
remaining = budget.get_remaining_budget()
```

### Expense Tracking

Expenses belong to budgets and can have:
- **Category** - Housing, Food, Transportation, etc.
- **Tag** - Payment method or custom tag
- **Sub-expenses** - Detailed breakdowns
- **Recurring flag** - Copied to next month's budget

### Debt Tracking

Track borrowed money and repayments:

```python
# Create a debt
debt = Debt.objects.create(
    user=user,
    name="Car Loan",
    total_amount=Decimal("50000.00")
)

# Add borrowing transaction
DebtTransaction.objects.create(
    debt=debt,
    amount=Decimal("10000.00"),
    date=date.today()
)

# Check repayment progress
print(f"Repaid: {debt.repayment_progress_percentage}%")
```

### Goal Setting

Set and track financial goals:

```python
goal = Goal.objects.create(
    user=user,
    name="Emergency Fund",
    target_amount=Decimal("100000.00"),
    target_date=date(2025, 12, 31)
)

# Add contribution
GoalContribution.objects.create(
    goal=goal,
    amount=Decimal("5000.00"),
    source="salary"
)

# Check if on track
print(f"On track: {goal.is_on_track()}")
```

---

## Script Runner

The `script_runner` app provides centralized script management.

### Commands

```bash
# List all available scripts
python manage.py list_scripts

# List scripts with execution history
python manage.py list_scripts --history

# Run a specific script
python manage.py <script_name> [args]
python manage.py backup_data --output backup.json
python manage.py build_apk --check

# Run all deploy scripts for current version
python manage.py run_scripts

# Dry run (see what would run)
python manage.py run_scripts --dry-run

# List what would run
python manage.py run_scripts --list
```

### Available Scripts

| Script | Category | Deploy | Description |
|--------|----------|--------|-------------|
| `build_apk` | Build & Deploy | No | Build Android APKs |
| `backup_data` | Data Management | No | Backup to JSON |
| `restore_data` | Data Management | No | Restore from JSON |
| `setup_superuser` | User Management | No | Create superuser |
| `assign_data_to_user` | User Management | No | Assign orphaned data |
| `create_default_categories` | Setup | **Yes** | Create default categories |
| `create_tags_from_expenses` | Migration | **Yes** | Migrate tags (v1.0-1.1) |
| `migrate_expense_tags_to_foreign_key` | Migration | **Yes** | Migrate FK (v1.0-1.1) |
| `archive_old_budgets` | Maintenance | No | Archive old budgets |
| `cleanup_budgets` | Maintenance | No | Clean invalid budgets |
| `cleanup_migrations` | Database | No | Drop tables (⚠️ DANGEROUS) |

### Version-Based Execution

Scripts can be version-specific:

```python
# In script_runner/registry.py
register_script(Script(
    name="migrate_expense_tags_to_foreign_key",
    description="Migrate expense tags to foreign key references",
    category="Migration",
    min_version="1.0.0",  # Only run for >= 1.0.0
    max_version="1.1.0",  # Only run for <= 1.1.0
    run_on_deploy=True,   # Include in run_scripts
    order=21,             # Run order
))
```

---

## API Reference

### Authentication

All API endpoints require authentication:

```bash
# Get auth token
curl -X POST http://localhost:8000/api-token-auth/ \
  -d "username=user@example.com&password=secret"

# Use token
curl -H "Authorization: Token YOUR_TOKEN" \
  http://localhost:8000/api/budgets/
```

### Endpoints

| Endpoint | Methods | Description |
|----------|---------|-------------|
| `/api/budgets/` | GET, POST | List/create budgets |
| `/api/budgets/{id}/` | GET, PUT, DELETE | Budget detail |
| `/api/goals/` | GET, POST | List/create goals |
| `/api/goals/{id}/` | GET, PUT, DELETE | Goal detail |
| `/api/goals/{id}/statistics/` | GET | Goal statistics |
| `/api/goals/{id}/add_contribution/` | POST | Add contribution |
| `/api/contributions/` | GET, POST | List/create contributions |

---

## Android APK Building

### Prerequisites

1. Android SDK installed
2. `ANDROID_HOME` environment variable set
3. Capacitor initialized (`npx cap add android`)

### Build Commands

```bash
# Check configuration
python manage.py build_apk --check

# Build both APKs
python manage.py build_apk

# Build specific variant
python manage.py build_apk --local   # Localhost APK
python manage.py build_apk --ngrok   # Ngrok APK

# Or use npm scripts
cd capacitor-app
npm run build          # Both
npm run build:local    # Localhost only
npm run build:ngrok    # Ngrok only
```

### Output

APKs are saved to `capacitor-app/output/`:
- `monai-local.apk` - Connects to local server
- `monai-ngrok.apk` - Connects to ngrok URL

---

## Development Guidelines

### Code Style

- Follow PEP 8 for Python
- Use type hints
- Maximum line length: 100 characters
- Use named `{% endblock %}`s in templates

### View Organization

Views are organized in `budgetapp/minimal/views/`:

```python
# Always use class-based views
class MyView(LoginRequiredView):
    def get(self, request, *args, **kwargs):
        # Implementation
        pass
```

### Adding New Scripts

1. Create management command in `budgetapp/management/commands/`
2. Register in `script_runner/registry.py`:

```python
register_script(Script(
    name="my_script",
    description="What it does",
    category="Category",
    example="my_script --arg value",
    run_on_deploy=False,  # Set True if should run with run_scripts
))
```

### JavaScript Libraries

| Library | Use For |
|---------|---------|
| Alpine.js | Simple UI state, toggles, forms |
| Anime.js | Complex animations |
| jQuery | AJAX, DOM manipulation |
| Bootstrap 5 | Layout, components |

---

## Database Schema

### Core Models

```
Budget
├── user (FK → CustomUser)
├── month (DateField)
├── income (DecimalField)
├── currency (CharField)
└── expenses (→ Expense)

Expense
├── budget (FK → Budget)
├── name, amount
├── category (FK → Category)
├── tag_foreign_key (FK → Tag)
├── is_recurring (BooleanField)
└── sub_expenses (→ SubExpense)

SubExpense
├── expense (FK → Expense)
├── name, amount
└── is_return (BooleanField)

Goal
├── user (FK → CustomUser)
├── name, description
├── target_amount, current_amount
├── target_date
└── contributions (→ GoalContribution)

Debt
├── user (FK → CustomUser)
├── name, total_amount
├── borrowed_amount
├── debt_tag (FK → Tag)
└── transactions (→ DebtTransaction)
```

---

## Deployment

### Production Checklist

1. **Configuration**
   - [ ] Set `app.debug: false`
   - [ ] Set strong `app.secret_key` (50+ chars)
   - [ ] Configure `email.backend: smtp`
   - [ ] Set proper `allowed_hosts`

2. **Database**
   - [ ] Use PostgreSQL
   - [ ] Run `python manage.py migrate`

3. **Static Files**
   - [ ] Run `python manage.py collectstatic`

4. **Scripts**
   - [ ] Run `python manage.py run_scripts`

5. **Security**
   - [ ] Enable HTTPS
   - [ ] Set secure cookies
   - [ ] Configure CORS properly

### Running Deploy Scripts

```bash
# See what would run
python manage.py run_scripts --list

# Run all deploy scripts
python manage.py run_scripts

# Continue even if one fails
python manage.py run_scripts --continue-on-error
```

---

## Archived Documentation

The following legacy docs are kept for reference but may be outdated:

- `ai_goal_assistant_*.md` - AI assistant planning docs
- `goals_feature*.md` - Goals feature implementation
- `planning_for_borrow_system.md` - Debt system planning
- `minimal_theme_development_guidelines.md` - Theme guidelines

---

## Support

For issues or questions:
1. Check this documentation first
2. Review existing code patterns
3. Search issue tracker
4. Create a new issue with reproduction steps

---

*This documentation is the single source of truth for the monAI Budget Tracker project.*

