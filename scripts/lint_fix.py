#!/usr/bin/env python3
"""
Script to help fix linting issues in the Django Budget Tracker project.
"""

import argparse
import subprocess  # nosec B404 - Required for running pre-commit
import sys
from pathlib import Path


def run_command(cmd, capture_output=True):
    """Run a command and return its output."""
    try:
        # We're only running pre-commit commands with fixed arguments
        # nosec B603 - Command args are controlled by the script
        result = subprocess.run(cmd, capture_output=capture_output, text=True, check=False)  # nosec
        return result
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {' '.join(cmd)}")
        print(e.stderr)
        return None


def check_prerequisites():
    """Check if pre-commit is installed."""
    result = run_command(["pre-commit", "--version"])
    if result and result.returncode == 0:
        print(f"pre-commit version: {result.stdout.strip()}")
    else:
        print("pre-commit not found. Please install it with:")
        print("pip install pre-commit")
        return False

    # Check if pre-commit hooks are installed
    hooks_dir = Path(".git/hooks")
    if not (hooks_dir / "pre-commit").exists():
        print("pre-commit hook not installed. Installing now...")
        run_command(["pre-commit", "install"], capture_output=False)

    return True


def run_formatters(files=None, all_files=False):
    """Run auto-formatters on specified files or all files."""
    # Basic formatters
    formatters = ["black", "isort", "prettier"]

    cmd = ["pre-commit", "run"]
    cmd.extend(formatters)

    if all_files:
        cmd.append("--all-files")
    elif files:
        cmd.append("--files")
        cmd.extend(files)

    print("Running formatters...")
    result = run_command(cmd, capture_output=False)
    return result.returncode == 0 if result else False


def run_linters(files=None, all_files=False, fix=False):
    """Run linters on specified files or all files."""
    # All linters (no longer 'manual')
    linters = ["flake8", "djlint-django", "bandit"]

    for linter in linters:
        cmd = ["pre-commit", "run", linter]

        if all_files:
            cmd.append("--all-files")
        elif files:
            cmd.append("--files")
            cmd.extend(files)

        print(f"Running {linter}...")
        run_command(cmd, capture_output=False)

    # Special case for djlint with --fix option
    if fix:
        print("Attempting to fix djlint issues...")
        for path in files or []:
            if path.endswith(".html"):
                run_command(["djlint", path, "--reformat"], capture_output=False)


def fix_common_issues(files=None):
    """Fix common issues in files."""
    if not files:
        return

    for file_path in files:
        if file_path.endswith(".html"):
            print(f"Attempting to fix common HTML issues in {file_path}...")
            # Add missing endblock names
            try:
                with open(file_path, "r") as f:
                    content = f.read()

                # Replace {% endblock %} with {% endblock content %} - basic approach
                if "{% endblock %}" in content and "{% block content %}" in content:
                    content = content.replace("{% endblock %}", "{% endblock content %}")

                    with open(file_path, "w") as f:
                        f.write(content)
                    print(f"  Fixed endblock tags in {file_path}")
            except Exception as e:
                print(f"Error fixing HTML issues in {file_path}: {e}")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Run linters and formatters for the Django Budget Tracker project."
    )
    parser.add_argument("-a", "--all", action="store_true", help="Run on all files in the project")
    parser.add_argument(
        "-f", "--fix", action="store_true", help="Try to automatically fix issues where possible"
    )
    parser.add_argument("files", nargs="*", help="Files to check (if not using --all)")

    args = parser.parse_args()

    if not args.all and not args.files:
        parser.print_help()
        return 1

    if not check_prerequisites():
        return 1

    # Run formatters first (these will fix most issues)
    if args.fix:
        run_formatters(args.files, args.all)

        # Try to fix some common issues that formatters don't handle
        if args.files:
            fix_common_issues(args.files)

    # Then run linters to check for remaining issues
    run_linters(args.files, args.all, args.fix)

    print(
        """
Linting completed. For help with common issues:
1. Check docs/code_formatting.md for guidance
2. For Python issues, use 'black' and 'isort' to auto-format
3. For HTML issues, consider using 'djlint --reformat' to auto-format
4. Add CSS classes instead of inline styles

To fix inline styles in HTML templates:
- Create CSS classes in appropriate .css files
- Replace style="width: X%" with class="some-class-name"
"""
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
