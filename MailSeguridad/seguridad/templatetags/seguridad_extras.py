from __future__ import annotations

from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def dict_key(d, key: str):
    """Return d[key], falling back to getattr(d, key) for model instances."""
    if d is None:
        return None
    # Try dict-style access first
    try:
        return d[key]
    except (KeyError, TypeError):
        pass
    # Fall back to attribute access (e.g. Django model instances)
    try:
        return getattr(d, key)
    except AttributeError:
        return None


@register.filter
def attr(obj, name: str):
    """Return getattr(obj, name)."""
    if obj is None:
        return None
    try:
        return getattr(obj, name)
    except (AttributeError, TypeError):
        return None


@register.filter
def dictget(d: dict, key: str):
    """Return d[key] — alias for dict_key, compatible with miGTD naming."""
    return dict_key(d, key)


@register.filter(is_safe=True)
def render_links(value):
    """Render ``=HYPERLINK(url, text)`` formulas as clickable HTML links.

    Usage in templates::

        {{ field_value|render_links }}

    The output is marked as safe HTML so the ``<a>`` tags are not escaped.
    """
    if value is None:
        return ""
    from seguridad.table_manager import render_hyperlinks

    return mark_safe(render_hyperlinks(str(value)))
