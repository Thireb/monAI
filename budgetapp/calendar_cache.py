"""Redis-backed cache for dashboard calendar HTML and template context.

Uses a per-user version counter so invalidation is O(1) when budgets change.
"""

from __future__ import annotations

from typing import Any

from django.core.cache import cache

_VERSION_KEY = "calendar_cache_version:{user_id}"
_YEAR_KEY = "calendar_year:{user_id}:{year}:v{version}"


def _version_cache_key(user_id: int) -> str:
    """Build the Redis key for a user's cache version counter."""
    return _VERSION_KEY.format(user_id=user_id)


def _year_cache_key(user_id: int, year: int, version: int) -> str:
    """Build the Redis key for a cached calendar year payload."""
    return _YEAR_KEY.format(user_id=user_id, year=year, version=version)


def get_user_cache_version(user_id: int) -> int:
    """Return the current cache version for a user (0 when unset)."""
    return cache.get(_version_cache_key(user_id), 0)


def bump_user_cache_version(user_id: int) -> None:
    """Drop all cached calendar entries for a user (budget create/update/delete)."""
    key = _version_cache_key(user_id)
    try:
        cache.incr(key)
    except ValueError:
        cache.set(key, 1, timeout=None)


def get_cached_calendar_year(user_id: int, year: int) -> dict[str, Any] | None:
    """Return cached calendar context for a user/year, or ``None`` on miss."""
    version = get_user_cache_version(user_id)
    return cache.get(_year_cache_key(user_id, year, version))


def set_cached_calendar_year(user_id: int, year: int, payload: dict[str, Any]) -> None:
    """Store calendar context for a user/year at the current cache version."""
    version = get_user_cache_version(user_id)
    cache.set(_year_cache_key(user_id, year, version), payload)
