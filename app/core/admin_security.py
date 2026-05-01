import hmac

from fastapi import Header, HTTPException, status

from app.core.config import settings


async def verify_admin_key(
    x_admin_key: str | None = Header(default=None, alias="X-Admin-Key"),
) -> None:
    if not x_admin_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing admin key.",
        )

    if not hmac.compare_digest(x_admin_key, settings.SENTINEL_ADMIN_KEY):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin key.",
        )