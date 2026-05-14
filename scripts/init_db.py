import asyncio

from app.integrations.db import engine
from app.models.user import Base


async def main() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    print("Database tables initialized successfully.")
    print("Note: For production, prefer: alembic upgrade head")


if __name__ == "__main__":
    asyncio.run(main())