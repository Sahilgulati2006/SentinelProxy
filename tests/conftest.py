import os
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Force test-safe environment variables before app imports
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./sentinelproxy_test.db"
os.environ["API_KEY_PEPPER"] = "test_pepper"
os.environ["SENTINEL_ADMIN_KEY"] = "test_admin_key"
os.environ["REDIS_URL"] = "redis://localhost:6379/15"
os.environ["RATE_LIMIT_REQUESTS"] = "1000"
os.environ["RATE_LIMIT_WINDOW_SECONDS"] = "60"

from app.integrations.db import get_db_session
from app.main import app
from app.models.user import Base


TEST_DATABASE_URL = os.environ["DATABASE_URL"]

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    future=True,
)

TestSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def override_get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with TestSessionLocal() as session:
        yield session


@pytest.fixture(autouse=True)
def override_fastapi_dependencies():
    app.dependency_overrides[get_db_session] = override_get_db_session
    yield
    app.dependency_overrides.clear()


@pytest_asyncio.fixture(autouse=True)
async def reset_test_database() -> AsyncGenerator[None, None]:
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)