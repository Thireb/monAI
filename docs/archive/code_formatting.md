# Code Formatting Guidelines

This document provides detailed information about the code formatting tools and standards used in the Django Budget Tracker project.

## Pre-commit Setup

The project uses [pre-commit](https://pre-commit.com/) to automatically format and check code before committing. This ensures consistent code style across the project.

### Installation

1. Install pre-commit (if not already installed):
   ```bash
   pip install pre-commit
   ```

2. Install the git hooks:
   ```bash
   pre-commit install
   ```

### Active Hooks

The following hooks run automatically on every commit and only on the files you've changed:

1. **Black** - Python code formatter
2. **isort** - Python import sorter
3. **flake8** - Python code linter with Django-specific checks
4. **djLint** - Django HTML template linter and formatter
5. **Prettier** - JavaScript and CSS formatter
6. **bandit** - Python security linter
7. **Pre-commit-hooks** - Various small checks for:
   - Trailing whitespace
   - End-of-file fixing
   - Debug statements
   - YAML syntax
   - Large file additions

### Running Hooks Manually

You can run any hook manually on specific files:

```bash
pre-commit run flake8 --files path/to/file.py
pre-commit run djlint-django --files path/to/template.html
pre-commit run bandit --files path/to/file.py
```

Or run all hooks on all files:

```bash
pre-commit run --all-files
```

## Common Issues and Solutions

### Python Issues (flake8)

1. **Unused imports (F401)**
   - Remove unused imports or mark them with `# noqa: F401` if needed for side effects

2. **Line too long (E501)**
   - Break long lines to be less than 100 characters
   - Use parentheses for multi-line expressions
   - Use line continuation for strings

3. **Django specific (DJ01)**
   - Avoid using `null=True` on string-based fields like TextField, CharField

### HTML Template Issues (djLint)

1. **Inline styles (H021)**
   - Move inline styles to CSS files
   - Create classes for commonly used styles
   - Example template fix:
     ```html
     <!-- Before -->
     <th style="width: 30%">Name</th>

     <!-- After -->
     <th class="col-name">Name</th>
     ```

     And in CSS:
     ```css
     .col-name {
       width: 30%;
     }
     ```

2. **Template tag formatting (T002, T003)**
   - Use double quotes in template tags: `{% extends "base.html" %}`
   - Add block names to endblock tags: `{% endblock content %}`

## Fixing Common Linting Errors

### HTML Template Errors

1. **Meta description (H030) and meta keywords (H031)**:
   Add meta tags in the head section:
   ```html
   <head>
     <meta name="description" content="A personal budget tracking application to help manage expenses and income">
     <meta name="keywords" content="budget, expenses, finance, tracking, money management">
     <!-- other meta tags -->
   </head>
   ```

2. **Orphan tag (H025)**:
   This usually means a tag is misplaced or not closed properly.

3. **Endblock with name (T003)**:
   ```html
   <!-- Instead of -->
   {% endblock %}

   <!-- Use -->
   {% endblock content %}
   ```

### Python Errors

1. **Fix all flake8 issues in a file**:
   ```bash
   python scripts/lint_fix.py -f path/to/file.py
   ```

## Helper Tools

### Using the lint_fix.py Script

The project includes a helper script to assist with fixing linting issues:

```bash
# Fix issues in specific files
python scripts/lint_fix.py -f file1.py file2.py

# Check all files in the project
python scripts/lint_fix.py -a

# Check and fix all files in the project
python scripts/lint_fix.py -a -f
```

## Custom Configuration

### .flake8

The configuration for flake8 is in `.flake8` in the project root. You can adjust:
- Maximum line length
- Ignored rules
- Per-file ignores

### .djlintrc

The configuration for Django template linting is in `.djlintrc`. You can adjust:
- Ignored rules
- Indentation
- Quote style

### .prettierrc

Configuration for JavaScript and CSS formatting in `.prettierrc`. You can adjust:
- Print width
- Tab width
- Quote style

### .isort.cfg

Configuration for Python import sorting in `.isort.cfg`. You can adjust:
- Known first-party modules
- Import sections order
- Line length
