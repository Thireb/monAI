"""
Script Registry - Central configuration for all runnable scripts.

Each script has:
- name: The Django management command name
- description: What the script does
- category: Grouping for display
- min_version: Minimum code version this script applies to (optional)
- max_version: Maximum code version this script applies to (optional)
- run_on_deploy: Whether to run this script during run_scripts (version-based run)
- dangerous: Whether the script requires extra confirmation
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Script:
    """Definition of a runnable script."""

    name: str
    description: str
    category: str
    example: str = ""
    min_version: Optional[str] = None
    max_version: Optional[str] = None
    run_on_deploy: bool = False
    dangerous: bool = False
    order: int = 100  # Lower number = runs first

    def matches_version(self, version: str) -> bool:
        """Check if this script applies to the given version."""
        if not self.min_version and not self.max_version:
            return True

        # Simple version comparison (works for semantic versioning)
        if self.min_version and version < self.min_version:
            return False
        if self.max_version and version > self.max_version:
            return False

        return True


# Registry of all available scripts
SCRIPT_REGISTRY: dict[str, Script] = {}


def register_script(script: Script) -> None:
    """Register a script in the registry."""
    SCRIPT_REGISTRY[script.name] = script


def get_script(name: str) -> Optional[Script]:
    """Get a script by name."""
    return SCRIPT_REGISTRY.get(name)


def get_all_scripts() -> list[Script]:
    """Get all registered scripts."""
    return list(SCRIPT_REGISTRY.values())


def get_scripts_for_version(version: str, deploy_only: bool = True) -> list[Script]:
    """Get all scripts that match a version, sorted by order."""
    scripts = [
        s for s in SCRIPT_REGISTRY.values()
        if s.matches_version(version) and (not deploy_only or s.run_on_deploy)
    ]
    return sorted(scripts, key=lambda s: s.order)


def get_scripts_by_category() -> dict[str, list[Script]]:
    """Get all scripts grouped by category."""
    by_category: dict[str, list[Script]] = {}
    for script in SCRIPT_REGISTRY.values():
        if script.category not in by_category:
            by_category[script.category] = []
        by_category[script.category].append(script)
    return by_category


# =============================================================================
# Register all scripts
# =============================================================================

# Build & Deploy
register_script(Script(
    name="build_apk",
    description="Build Android APKs for the Capacitor app",
    category="Build & Deploy",
    example="build_apk --local",
    run_on_deploy=False,  # Manual only
))

# Data Management
register_script(Script(
    name="backup_data",
    description="Backup all budget-related data to JSON",
    category="Data Management",
    example="backup_data --output my_backup.json",
    run_on_deploy=False,
))

register_script(Script(
    name="restore_data",
    description="Restore data from a JSON backup file",
    category="Data Management",
    example="restore_data backup.json",
    run_on_deploy=False,
))

# User Management
register_script(Script(
    name="setup_superuser",
    description="Create initial superuser from config or interactively",
    category="User Management",
    example="setup_superuser",
    run_on_deploy=False,
))

register_script(Script(
    name="assign_data_to_user",
    description="Assign orphaned data to a specific user",
    category="User Management",
    example="assign_data_to_user --email user@example.com",
    run_on_deploy=False,
))

# Setup Scripts (run on deploy)
register_script(Script(
    name="create_default_categories",
    description="Create default expense categories for users",
    category="Setup",
    example="create_default_categories --all-users",
    run_on_deploy=True,
    order=10,
))

# Migration Scripts (version-specific)
register_script(Script(
    name="create_tags_from_expenses",
    description="Create tags from existing expense tag values",
    category="Migration",
    example="create_tags_from_expenses",
    min_version="1.0.0",
    max_version="1.1.0",
    run_on_deploy=True,
    order=20,
))

register_script(Script(
    name="migrate_expense_tags_to_foreign_key",
    description="Migrate expense tags to foreign key references",
    category="Migration",
    example="migrate_expense_tags_to_foreign_key",
    min_version="1.0.0",
    max_version="1.1.0",
    run_on_deploy=True,
    order=21,
))

# Maintenance
register_script(Script(
    name="archive_old_budgets",
    description="Archive budgets from previous years",
    category="Maintenance",
    example="archive_old_budgets",
    run_on_deploy=False,
))

register_script(Script(
    name="cleanup_budgets",
    description="Cleanup empty or invalid budgets",
    category="Maintenance",
    example="cleanup_budgets",
    run_on_deploy=False,
))

# Database (dangerous)
register_script(Script(
    name="cleanup_migrations",
    description="Drop database tables (DANGEROUS - development only)",
    category="Database",
    example="cleanup_migrations --dry-run",
    dangerous=True,
    run_on_deploy=False,
))

