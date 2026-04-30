from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import verify_api_key
from app.integrations.db import get_db_session
from app.schemas.auth import AuthenticatedUser


async def get_current_user(
    authorization: str | None = Header(default=None),
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
    session: AsyncSession = Depends(get_db_session),
) -> AuthenticatedUser:
    return await verify_api_key(
        authorization=authorization,
        x_api_key=x_api_key,
        session=session,
    )