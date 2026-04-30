import asyncio

from app.core.api_keys import generate_api_key, hash_api_key
from app.core.config import settings
from app.integrations.db import AsyncSessionLocal, engine
from app.models.user import Base
from app.repositories.user_repo import UserRepository


async def main() -> None:
    repo = UserRepository()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        user = await repo.get_user_by_email(
            session,
            settings.BOOTSTRAP_ADMIN_EMAIL,
        )

        if user is None:
            user = await repo.create_user(
                session,
                email=settings.BOOTSTRAP_ADMIN_EMAIL,
                monthly_token_limit=settings.BOOTSTRAP_MONTHLY_TOKEN_LIMIT,
            )

        full_key, prefix = generate_api_key()
        key_hash = hash_api_key(full_key)

        await repo.create_api_key(
            session,
            user_id=user.id,
            key_prefix=prefix,
            key_hash=key_hash,
            name="local-bootstrap-key",
        )

        await session.commit()

    print("\nBootstrap complete.")
    print("Save this API key now. It will not be shown again:\n")
    print(full_key)
    print()


if __name__ == "__main__":
    asyncio.run(main())