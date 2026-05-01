from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.admin_deps import RequireAdminKey
from app.core.api_keys import generate_api_key, hash_api_key
from app.integrations.db import get_db_session
from app.repositories.user_repo import UserRepository
from app.schemas.admin import (
    APIKeyResponse,
    CreateAPIKeyRequest,
    CreateAPIKeyResponse,
    CreateUserRequest,
    UpdateBudgetRequest,
    UserResponse,
)

router = APIRouter(prefix="/v1/admin", tags=["admin"])
repo = UserRepository()


@router.post(
    "/users",
    response_model=UserResponse,
    dependencies=[RequireAdminKey],
)
async def create_user(
    payload: CreateUserRequest,
    session: AsyncSession = Depends(get_db_session),
):
    existing = await repo.get_user_by_email(session, payload.email)
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already exists.",
        )

    user = await repo.create_user(
        session=session,
        email=payload.email,
        monthly_token_limit=payload.monthly_token_limit,
    )
    await session.commit()

    return UserResponse(
        id=user.id,
        email=user.email,
        monthly_token_limit=user.monthly_token_limit,
        is_active=user.is_active,
        created_at=user.created_at,
    )


@router.get(
    "/users",
    response_model=list[UserResponse],
    dependencies=[RequireAdminKey],
)
async def list_users(
    session: AsyncSession = Depends(get_db_session),
):
    users = await repo.list_users(session)

    return [
        UserResponse(
            id=user.id,
            email=user.email,
            monthly_token_limit=user.monthly_token_limit,
            is_active=user.is_active,
            created_at=user.created_at,
        )
        for user in users
    ]


@router.patch(
    "/users/{user_id}/budget",
    response_model=UserResponse,
    dependencies=[RequireAdminKey],
)
async def update_user_budget(
    user_id: str,
    payload: UpdateBudgetRequest,
    session: AsyncSession = Depends(get_db_session),
):
    user = await repo.update_user_budget(
        session=session,
        user_id=user_id,
        monthly_token_limit=payload.monthly_token_limit,
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    await session.commit()

    return UserResponse(
        id=user.id,
        email=user.email,
        monthly_token_limit=user.monthly_token_limit,
        is_active=user.is_active,
        created_at=user.created_at,
    )


@router.post(
    "/api-keys",
    response_model=CreateAPIKeyResponse,
    dependencies=[RequireAdminKey],
)
async def create_api_key(
    payload: CreateAPIKeyRequest,
    session: AsyncSession = Depends(get_db_session),
):
    user = await repo.get_user_by_id(session, payload.user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    full_key, prefix = generate_api_key()
    key_hash = hash_api_key(full_key)

    api_key = await repo.create_api_key(
        session=session,
        user_id=user.id,
        key_prefix=prefix,
        key_hash=key_hash,
        name=payload.name,
    )

    await session.commit()

    return CreateAPIKeyResponse(
        id=api_key.id,
        user_id=api_key.user_id,
        key_prefix=api_key.key_prefix,
        name=api_key.name,
        is_active=api_key.is_active,
        api_key=full_key,
    )


@router.get(
    "/api-keys",
    response_model=list[APIKeyResponse],
    dependencies=[RequireAdminKey],
)
async def list_api_keys(
    session: AsyncSession = Depends(get_db_session),
):
    api_keys = await repo.list_api_keys(session)

    return [
        APIKeyResponse(
            id=api_key.id,
            user_id=api_key.user_id,
            key_prefix=api_key.key_prefix,
            name=api_key.name,
            is_active=api_key.is_active,
            created_at=api_key.created_at,
        )
        for api_key in api_keys
    ]


@router.post(
    "/api-keys/{key_id}/revoke",
    response_model=APIKeyResponse,
    dependencies=[RequireAdminKey],
)
async def revoke_api_key(
    key_id: str,
    session: AsyncSession = Depends(get_db_session),
):
    api_key = await repo.revoke_api_key(session, key_id)

    if api_key is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found.",
        )

    await session.commit()

    return APIKeyResponse(
        id=api_key.id,
        user_id=api_key.user_id,
        key_prefix=api_key.key_prefix,
        name=api_key.name,
        is_active=api_key.is_active,
        created_at=api_key.created_at,
    )

@router.post(
    "/users/{user_id}/deactivate",
    response_model=UserResponse,
    dependencies=[RequireAdminKey],
)
async def deactivate_user(
    user_id: str,
    session: AsyncSession = Depends(get_db_session),
):
    user = await repo.deactivate_user(
        session=session,
        user_id=user_id,
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    await session.commit()

    return UserResponse(
        id=user.id,
        email=user.email,
        monthly_token_limit=user.monthly_token_limit,
        is_active=user.is_active,
        created_at=user.created_at,
    )