from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import APIKey, User


class UserRepository:
    async def get_user_by_email(
        self,
        session: AsyncSession,
        email: str,
    ) -> User | None:
        result = await session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def get_user_by_id(
        self,
        session: AsyncSession,
        user_id: str,
    ) -> User | None:
        result = await session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def list_users(
        self,
        session: AsyncSession,
    ) -> list[User]:
        result = await session.execute(
            select(User).order_by(User.created_at.desc())
        )
        return list(result.scalars().all())

    async def create_user(
        self,
        session: AsyncSession,
        email: str,
        monthly_token_limit: int,
    ) -> User:
        user = User(
            email=email,
            monthly_token_limit=monthly_token_limit,
            is_active=True,
        )
        session.add(user)
        await session.flush()
        return user

    async def update_user_budget(
        self,
        session: AsyncSession,
        user_id: str,
        monthly_token_limit: int,
    ) -> User | None:
        user = await self.get_user_by_id(session, user_id)
        if user is None:
            return None

        user.monthly_token_limit = monthly_token_limit
        await session.flush()
        return user

    async def get_api_key_by_prefix(
        self,
        session: AsyncSession,
        key_prefix: str,
    ) -> APIKey | None:
        result = await session.execute(
            select(APIKey).where(APIKey.key_prefix == key_prefix)
        )
        return result.scalar_one_or_none()

    async def list_api_keys(
        self,
        session: AsyncSession,
    ) -> list[APIKey]:
        result = await session.execute(
            select(APIKey).order_by(APIKey.created_at.desc())
        )
        return list(result.scalars().all())

    async def list_api_keys_for_user(
        self,
        session: AsyncSession,
        user_id: str,
    ) -> list[APIKey]:
        result = await session.execute(
            select(APIKey)
            .where(APIKey.user_id == user_id)
            .order_by(APIKey.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_api_key_by_id(
        self,
        session: AsyncSession,
        key_id: str,
    ) -> APIKey | None:
        result = await session.execute(
            select(APIKey).where(APIKey.id == key_id)
        )
        return result.scalar_one_or_none()

    async def create_api_key(
        self,
        session: AsyncSession,
        user_id: str,
        key_prefix: str,
        key_hash: str,
        name: str,
    ) -> APIKey:
        api_key = APIKey(
            user_id=user_id,
            key_prefix=key_prefix,
            key_hash=key_hash,
            name=name,
            is_active=True,
        )
        session.add(api_key)
        await session.flush()
        return api_key
    
    async def deactivate_user(
        self,
        session: AsyncSession,
        user_id: str,
    ) -> User | None:
        user = await self.get_user_by_id(session, user_id)
        if user is None:
            return None

        user.is_active = False

        api_keys = await self.list_api_keys_for_user(session, user_id)
        for api_key in api_keys:
            api_key.is_active = False

        await session.flush()
        return user

    async def revoke_api_key(
        self,
        session: AsyncSession,
        key_id: str,
    ) -> APIKey | None:
        api_key = await self.get_api_key_by_id(session, key_id)
        if api_key is None:
            return None

        api_key.is_active = False
        await session.flush()
        return api_key