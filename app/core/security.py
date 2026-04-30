import hmac

from fastapi import Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.api_keys import extract_key_prefix, hash_api_key
from app.models.user import APIKey, User
from app.repositories.user_repo import UserRepository
from app.schemas.auth import AuthenticatedUser


repo = UserRepository()


async def verify_api_key(
    authorization: str | None,
    x_api_key: str | None,
    session: AsyncSession,
) -> AuthenticatedUser:
    provided_key = None

    if authorization:
        scheme, _, token = authorization.partition(" ")
        if scheme.lower() == "bearer" and token:
            provided_key = token

    if not provided_key and x_api_key:
        provided_key = x_api_key

    if not provided_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key.",
        )

    key_prefix = extract_key_prefix(provided_key)
    api_key: APIKey | None = await repo.get_api_key_by_prefix(
        session,
        key_prefix,
    )

    if api_key is None or not api_key.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key.",
        )

    provided_hash = hash_api_key(provided_key)

    if not hmac.compare_digest(provided_hash, api_key.key_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key.",
        )

    user: User | None = await repo.get_user_by_id(session, api_key.user_id)

    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user.",
        )

    return AuthenticatedUser(
        user_id=user.id,
        email=user.email,
        api_key_prefix=api_key.key_prefix,
        monthly_token_limit=user.monthly_token_limit,
    )