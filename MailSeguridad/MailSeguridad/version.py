"""
Single source of truth for the MailSeguridad application version.

Bump this number on EVERY code change following semver:
  - MAJOR: breaking changes (DB schema, API, auth flow)
  - MINOR: new features (views, pages, functionality)
  - PATCH: bug fixes, UI tweaks, refactors

Always update this file + git commit + git tag when deploying.
"""

__version__ = "2.1.0"
VERSION = __version__  # alias for convenience
