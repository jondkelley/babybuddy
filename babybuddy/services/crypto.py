import base64
import hashlib
from typing import Optional

from django.conf import settings

try:
    from cryptography.fernet import Fernet  # type: ignore
except Exception:  # pragma: no cover
    Fernet = None  # optional dependency; fall back to no-op crypto


def _derive_key_from_secret(secret: str) -> bytes:
    # Deterministic 32-byte key from SECRET_KEY
    h = hashlib.sha256(secret.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(h)


def _fernet() -> Optional["Fernet"]:
    if Fernet is None:
        return None
    return Fernet(_derive_key_from_secret(settings.SECRET_KEY))


def encrypt(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    f = _fernet()
    if f is None:
        # Fallback: return original (not encrypted) when cryptography is unavailable
        return value
    return f.encrypt(value.encode("utf-8")).decode("utf-8")


def decrypt(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    f = _fernet()
    if f is None:
        # Fallback: return original when cryptography is unavailable
        return value
    return f.decrypt(value.encode("utf-8")).decode("utf-8")
