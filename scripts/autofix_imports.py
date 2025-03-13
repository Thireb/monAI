#!/usr/bin/env python3
"""
Script to automatically fix common issues in Python files, particularly unused imports.
Designed to work with the output of flake8.
"""

import re
import sys
from pathlib import Path


def find_unused_imports(file_path):
    """Find unused imports in a file using flake8."""
    import subprocess  # nosec B404 - Required for running pre-commit

    cmd = ["flake8", "--select=F401", file_path]
    result = subprocess.run(
        cmd, capture_output=True, text=True
    )  # nosec B603 - Command args are controlled by the script

    unused_imports = []
    for line in result.stdout.splitlines():
        match = re.search(r"F401 '([^']+)' imported but unused", line)
        if match:
            unused_imports.append(match.group(1))

    return unused_imports


def remove_unused_imports(file_path, unused_imports):
    """Remove unused imports from a file."""
    if not unused_imports:
        return False

    with open(file_path, "r") as f:
        lines = f.readlines()

    modified_lines = []
    changes_made = False

    for line in lines:
        skip_line = False
        for imp in unused_imports:
            # Handle import on its own line
            if re.search(rf"^import\s+{re.escape(imp)}$", line.strip()):
                skip_line = True
                changes_made = True
                break

            # Handle "from x import y" style
            module_match = re.search(r"from\s+([^\s]+)\s+import\s+(.+)", line)
            if module_match:
                module = module_match.group(1)
                imports = module_match.group(2)

                # If the exact import match is found in a from-import statement
                if imp == f"{module}.{imports.strip()}":
                    skip_line = True
                    changes_made = True
                    break

                # If the import is part of a multiple import statement
                if "," in imports:
                    import_parts = [p.strip() for p in imports.split(",")]
                    for i, part in enumerate(import_parts):
                        if f"{module}.{part}" == imp:
                            import_parts.pop(i)
                            if import_parts:
                                new_line = f"from {module} import {', '.join(import_parts)}\n"
                                modified_lines.append(new_line)
                            changes_made = True
                            skip_line = True
                            break

        if not skip_line:
            modified_lines.append(line)

    if changes_made:
        with open(file_path, "w") as f:
            f.writelines(modified_lines)
        return True

    return False


def fix_long_lines(file_path):
    """Fix long lines by breaking strings using parentheses where possible."""
    import subprocess  # nosec B404 - Required for running pre-commit

    from black import FileMode, format_str

    # Find long lines using flake8
    cmd = ["flake8", "--select=E501", file_path]
    result = subprocess.run(
        cmd, capture_output=True, text=True
    )  # nosec B603 - Command args are controlled by the script

    if not result.stdout:
        return False

    # Try to fix with black first
    try:
        with open(file_path, "r") as f:
            content = f.read()

        # Use black to format string
        mode = FileMode(line_length=100)
        formatted = format_str(content, mode=mode)

        with open(file_path, "w") as f:
            f.write(formatted)

        # Check if black fixed the issues
        result = subprocess.run(
            cmd, capture_output=True, text=True
        )  # nosec B603 - Command args are controlled by the script
        if not result.stdout:
            return True
    except Exception as e:
        print(f"Error using black to format {file_path}: {e}")

    return False


def main():
    if len(sys.argv) < 2:
        print("Usage: python autofix_imports.py <file_path> [file_path2 ...]")
        return 1

    files = sys.argv[1:]

    for file_path in files:
        path = Path(file_path)
        if not path.exists():
            print(f"File not found: {file_path}")
            continue

        print(f"Processing {file_path}...")

        # Fix unused imports
        unused_imports = find_unused_imports(file_path)
        if unused_imports:
            print(f"Found unused imports: {', '.join(unused_imports)}")
            if remove_unused_imports(file_path, unused_imports):
                print(f"  Fixed unused imports in {file_path}")

        # Fix long lines
        if fix_long_lines(file_path):
            print(f"  Fixed long lines in {file_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
