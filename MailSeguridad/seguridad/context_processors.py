from __future__ import annotations

from django.conf import settings


def active_context(request):
    """Adds app version to all templates."""
    return {
        "app_version": getattr(settings, "APP_VERSION", "0.0.0"),
    }
