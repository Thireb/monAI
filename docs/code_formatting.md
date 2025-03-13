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

By default, the following hooks are active and will run on every commit:

1. **Black** - Python code formatter
2. **isort** - Python import sorter
3. **Prettier** - JavaScript and CSS formatter
4. **Pre-commit-hooks** - Various small checks for:
   - Trailing whitespace
   - End-of-file fixing
   - Debug statements
   - YAML syntax
   - Large file additions

### Manual Hooks

The following hooks are available but disabled by default. They can be run manually:

1. **flake8** - Python code linter with Django-specific checks
2. **djLint** - Django HTML template linter and formatter
3. **bandit** - Python security linter

To run any of these manual hooks:

```bash
pre-commit run flake8 --all-files
pre-commit run djlint-django --all-files
pre-commit run bandit --all-files
```

Or run all hooks (including manual ones):

```bash
pre-commit run --all-hooks --all-files
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

## Gradual Integration

If you're working with an existing codebase, it's recommended to:

1. Start with automatic formatters only (the default configuration)
2. Gradually fix linting issues in small batches
3. Enable stricter checks as the codebase improves

To enable more strict checking for new files while ignoring existing issues:

```bash
pre-commit run --hook-stage manual --files path/to/new/file.py
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
