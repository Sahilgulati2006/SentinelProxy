import hashlib
import secrets

from app.core.config import settings


def generate_api_key() -> tuple[str, str]:
    """
    Returns: (full_key, prefix)
    Example full key: sp_live_xxxxx
    """
    secret = secrets.token_urlsafe(32)
    full_key = f"sp_live_{secret}"
    prefix = full_key[:16]
    return full_key, prefix


def hash_api_key(api_key: str) -> str:
    value = f"{api_key}.{settings.API_KEY_PEPPER}"
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def extract_key_prefix(api_key: str) -> str:
    return api_key[:16]