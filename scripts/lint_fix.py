#!/usr/bin/env python3
"""
Script to help fix linting issues in the Django Budget Tracker project.
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path


def run_command(cmd, capture_output=True):
    """Run a command and return its output."""
    try:
        result = subprocess.run(cmd, capture_output=capture_output, text=True, check=False)
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
    cmd = ["pre-commit", "run", "black", "isort", "prettier"]

    if all_files:
        cmd.append("--all-files")
    elif files:
        cmd.append("--files")
        cmd.extend(files)

    print("Running auto-formatters...")
    result = run_command(cmd, capture_output=False)
    return result.returncode == 0 if result else False


def run_linters(files=None, all_files=False, fix=False):
    """Run linters on specified files or all files."""
    hook_ids = ["flake8", "djlint-django", "bandit"]

    for hook_id in hook_ids:
        cmd = ["pre-commit", "run", hook_id]

        if all_files:
            cmd.append("--all-files")
        elif files:
            cmd.append("--files")
            cmd.extend(files)

        print(f"Running {hook_id}...")
        run_command(cmd, capture_output=False)

    # Special case for djlint with --fix option
    if fix:
        print("Attempting to fix djlint issues...")
        for path in files or []:
            if path.endswith(".html"):
                run_command(["djlint", path, "--reformat"], capture_output=False)


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

    # Run formatters first
    if args.fix:
        run_formatters(args.files, args.all)

    # Then run linters
    run_linters(args.files, args.all, args.fix)

    print(
        """
Linting completed. For help with common issues:
1. Check docs/code_formatting.md for guidance
2. For Python issues, consider using 'black' and 'isort' to auto-format
3. For HTML issues, consider using 'djlint --reformat' to auto-format
4. Add CSS classes instead of inline styles
"""
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
