"""Email configuration backed by a JSON file (same pattern as miGTD)."""

from __future__ import annotations

import base64
import json
from dataclasses import asdict, dataclass
from pathlib import Path

from cryptography.fernet import Fernet
from django.conf import settings


def _fernet_cipher() -> Fernet:
    key = base64.urlsafe_b64encode(
        settings.SECRET_KEY[:32].encode().ljust(32, b"\0")
    )
    return Fernet(key)


def _encrypt(raw: str) -> str:
    return _fernet_cipher().encrypt(raw.encode()).decode()


def _decrypt(encrypted: str) -> str:
    if not encrypted:
        return ""
    try:
        return _fernet_cipher().decrypt(encrypted.encode()).decode()
    except Exception:
        return ""


def _config_path() -> Path:
    config_dir = settings.BASE_DIR / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir / "email.json"


@dataclass
class EmailSettings:
    """SMTP configuration backed by a JSON file."""

    host: str = ""
    port: int = 587
    from_email: str = ""
    username: str = ""
    encrypted_password: str = ""
    use_starttls: bool = True
    encryption_type: str = "starttls"

    def set_password(self, raw: str) -> None:
        if raw:
            self.encrypted_password = _encrypt(raw)
        else:
            self.encrypted_password = ""

    def get_password(self) -> str:
        return _decrypt(self.encrypted_password)

    @classmethod
    def load(cls) -> EmailSettings:
        path = _config_path()
        if path.exists():
            try:
                data: dict = json.loads(path.read_text(encoding="utf-8"))
                return cls(**data)
            except (json.JSONDecodeError, TypeError, ValueError):
                pass
        return cls()

    def save(self) -> None:
        path = _config_path()
        path.write_text(
            json.dumps(asdict(self), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def is_configured(self) -> bool:
        return bool(self.host)

    def is_testable(self) -> bool:
        return bool(self.host) and bool(self.port)
