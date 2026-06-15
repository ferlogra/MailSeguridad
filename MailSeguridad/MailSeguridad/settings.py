from __future__ import annotations

import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

APP_VERSION = "1.0.0"

SECRET_KEY = os.environ.get(
    "MAILSEG_SECRET_KEY",
    "django-insecure-mailseg-dev-key-change-in-production",
)
DEBUG = os.environ.get("MAILSEG_DEBUG", "True").lower() == "true"
ALLOWED_HOSTS: list[str] = ["*"]

# ── Databases ────────────────────────────────────────────────────
# Default database: Django internals (users, configs, etc.)
# mail_seguridad: external SQLite DB created by get-Mail.ps1

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": str(BASE_DIR / "MailSeguridad" / "mail_seguridad.db"),
    },
}

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "seguridad.apps.SeguridadConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "seguridad.middleware.CurrentUserMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "MailSeguridad.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "seguridad.context_processors.active_context",
            ],
        },
    }
]

WSGI_APPLICATION = "MailSeguridad.wsgi.application"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "es"
TIME_ZONE = "Europe/Madrid"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "seguridad" / "static"]
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

# ── Email ──────────────────────────────────────────────────────
# Default: console backend. Override via env vars for real SMTP.
EMAIL_BACKEND = os.environ.get(
    "MAILSEG_EMAIL_BACKEND",
    "django.core.mail.backends.console.EmailBackend",
)
EMAIL_HOST = os.environ.get("MAILSEG_EMAIL_HOST", "")
EMAIL_PORT = int(os.environ.get("MAILSEG_EMAIL_PORT", "587"))
EMAIL_USE_TLS = os.environ.get("MAILSEG_EMAIL_USE_TLS", "True").lower() == "true"
EMAIL_HOST_USER = os.environ.get("MAILSEG_EMAIL_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("MAILSEG_EMAIL_PASSWORD", "")
DEFAULT_FROM_EMAIL = os.environ.get(
    "MAILSEG_DEFAULT_FROM", "noreply@mailseguridad.local"
)

# ── Password reset ─────────────────────────────────────────────
PASSWORD_RESET_TIMEOUT_MINUTES = int(
    os.environ.get("MAILSEG_PASSWORD_RESET_TIMEOUT", "10")
)

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
AUTH_USER_MODEL = "seguridad.User"
LOGIN_URL = "accounts_login"
LOGIN_REDIRECT_URL = "menu"
LOGOUT_REDIRECT_URL = "accounts_login"
