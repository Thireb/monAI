# monAI — Django Budget Tracker

A personal budget tracking application built with Django (monAI). This app helps you manage monthly expenses, track spending by categories and tags, and maintain a clear view of your financial health.

For maintainers, **full documentation** lives in **[docs/README.md](docs/README.md)** (configuration, deployment, APIs, and tooling).

## Features

- Monthly budget management
- Expense categorization and tag breakdown
- Income tracking with history
- Category-wise and tag-wise expense statistics
- Archive functionality for old budgets
- Recurring expense support
- Minimal theme UI (Alpine.js, Bootstrap)

## Prerequisites

- Python 3.11+ (see `requirements.txt` / `docs/README.md` for version notes)
- pip (Python package manager)
- virtualenv or pyenv (recommended)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/Thireb/monAI.git
cd monAI
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

4. Configuration — copy the template and edit (see [docs/README.md](docs/README.md)):
```bash
cp config.yaml.example config.yaml
```

5. Apply database migrations:
```bash
python manage.py migrate
```

6. Create an admin user (project uses `setup_superuser`; see docs):
```bash
python manage.py setup_superuser
```

7. Run the development server:
```bash
python manage.py runserver
```

The application will be available at `http://127.0.0.1:8000/` (minimal UI under `/minimal/`).

## Docker (optional)

You can run the project in a container with **Arch Linux**:

1. Ensure you have `config.yaml` in the project root (copy from `config.yaml.example` and adjust).
2. From the project root:
   ```bash
   docker compose up --build
   ```
3. Open **http://localhost:8000**. The container runs `migrate` then `runserver 0.0.0.0:8000`.

- **Dockerfile**: base image Arch Linux, system deps (Python, Cairo/Pango for WeasyPrint), virtualenv, `pip install`, then run the server.
- **docker-compose.yml**: builds the image and maps host port 8000 to container port 8000.
- **.dockerignore**: keeps the build context small (excludes venv, `.git`, etc.).

To run in the background: `docker compose up -d`. To stop: `docker compose down`.

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

1. Log in with your user credentials
2. Create categories for your expenses (e.g., Groceries, Rent, Utilities)
3. Create a new budget for the current month
4. Add your monthly income
5. Start tracking expenses by category and tag

## Project Structure

```
monAI/
├── accounts/              # Custom user and profile
├── budgetapp/           # Main application (models, views, minimal theme)
│   ├── minimal/         # Minimal theme views and templates
│   └── migrations/
├── budget_tracker/      # Django project (settings, config loader)
├── capacitor-app/       # Capacitor Android wrapper
├── script_runner/       # Script registry and deploy helpers
├── static/              # Static files (CSS, JS, images)
├── docs/                # Project documentation
├── manage.py
├── config.yaml.example  # Copy to config.yaml (gitignored)
└── requirements.txt
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
- Inspired by the need for a simple, focused budget tracking solution
