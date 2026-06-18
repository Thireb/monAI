"""Template tag for automatic static file versioning.

Generates static URLs with file modification time as query parameter
for cache busting without manual version updates.
"""

from __future__ import annotations

from django import template
from django.conf import settings
from django.templatetags.static import static

register = template.Library()


@register.simple_tag
def versioned_static(path: str) -> str:
    """Generate a static URL with a modification-time hash for cache busting.

    Args:
        path: Relative path under the static directory.

    Returns:
        Static URL, optionally suffixed with ``?h=<mtime>``.

    Example:
        In templates::

            {% load static_version %}
            <link rel="stylesheet" href="{% versioned_static 'css/theme.css' %}">
    """
    url = static(path)
    file_path = settings.BASE_DIR / "static" / path

    if file_path.exists():
        mtime = int(file_path.stat().st_mtime)
        return f"{url}?h={mtime}"

    return url
