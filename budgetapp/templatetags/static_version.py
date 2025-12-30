"""
Template tag for automatic static file versioning.

Generates static URLs with file modification time as query parameter
for cache busting without manual version updates.
"""

from django import template
from django.conf import settings
from django.templatetags.static import static

register = template.Library()


@register.simple_tag
def versioned_static(path):
    """
    Generate static URL with modification time hash for cache busting.

    Usage in templates:
        {% load static_version %}
        <link rel="stylesheet" href="{% versioned_static 'css/theme.css' %}">

    Output:
        /static/css/theme.css?h=1703945123

    The ?h= parameter changes when the file is modified, forcing browsers
    to fetch the new version instead of using cached content.
    """
    url = static(path)
    file_path = settings.BASE_DIR / 'static' / path

    if file_path.exists():
        # Use file modification time as version
        mtime = int(file_path.stat().st_mtime)
        return f"{url}?h={mtime}"

    return url

