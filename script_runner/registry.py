"""Central registry of runnable management scripts.

Each script has:
- name: The Django management command name
- description: What the script does
- category: Grouping for display
- min_version: Minimum code version this script applies to (optional)
- max_version: Maximum code version this script applies to (optional)
- run_on_deploy: Whether to run this script during run_scripts (version-based run)
- dangerous: Whether the script requires extra confirmation
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Script:
    """Definition of a runnable script."""

    name: str
    description: str
    category: str
    example: str = ""
    min_version: str | None = None
    max_version: str | None = None
    run_on_deploy: bool = False
    dangerous: bool = False
    order: int = 100  # Lower number = runs first

    def matches_version(self, version: str) -> bool:
        """Check if this script applies to the given version.

        Args:
            version: Application version string to compare.

        Returns:
            True when the version falls within configured min/max bounds.
        """
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
    """Register a script in the registry.

    Args:
        script: Script definition to add or replace by name.
    """
    SCRIPT_REGISTRY[script.name] = script


def get_script(name: str) -> Script | None:
    """Get a script by name.

    Args:
        name: Django management command name.

    Returns:
        Matching script definition, or None when not registered.
    """
    return SCRIPT_REGISTRY.get(name)


def get_all_scripts() -> list[Script]:
    """Get all registered scripts.

    Returns:
        List of every script in the registry.
    """
    return list(SCRIPT_REGISTRY.values())


def get_scripts_for_version(version: str, deploy_only: bool = True) -> list[Script]:
    """Get all scripts that match a version, sorted by order.

    Args:
        version: Application version string to match against script bounds.
        deploy_only: When True, include only scripts marked ``run_on_deploy``.

    Returns:
        Matching scripts sorted by ascending ``order``.
    """
    scripts = [
        s for s in SCRIPT_REGISTRY.values()
        if s.matches_version(version) and (not deploy_only or s.run_on_deploy)
    ]
    return sorted(scripts, key=lambda s: s.order)


def get_scripts_by_category() -> dict[str, list[Script]]:
    """Get all scripts grouped by category.

    Returns:
        Mapping of category name to scripts in that category.
    """
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
# (no build scripts registered)

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

# Setup Scripts (run on deploy)
register_script(Script(
    name="create_default_categories",
    description="Create default expense categories for users",
    category="Setup",
    example="create_default_categories --all-users",
    run_on_deploy=True,
    order=10,
))

# Maintenance
register_script(Script(
    name="archive_old_budgets",
    description="Archive budgets from previous years",
    category="Maintenance",
    example="archive_old_budgets",
    run_on_deploy=False,
))
