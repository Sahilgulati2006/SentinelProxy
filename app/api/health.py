from fastapi import APIRouter, HTTPException
from sqlalchemy import text

from app.integrations.db import AsyncSessionLocal
from app.integrations.redis_client import get_redis_client
from app.services.provider_health_service import ProviderHealthService

router = APIRouter()
provider_health_service = ProviderHealthService()


@router.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "SentinelProxy",
    }


@router.get("/ready")
async def ready():
    checks = {}

    # Redis check
    try:
        redis_client = get_redis_client()
        await redis_client.ping()
        checks["redis"] = "ok"
    except Exception as exc:
        checks["redis"] = f"error: {str(exc)}"

    # Database check
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as exc:
        checks["database"] = f"error: {str(exc)}"

    # Provider check
    provider_check = await provider_health_service.check()
    checks["provider"] = provider_check

    is_ready = (
        checks.get("redis") == "ok"
        and checks.get("database") == "ok"
        and provider_check.get("status") == "ok"
    )

    if not is_ready:
        raise HTTPException(
            status_code=503,
            detail={
                "status": "not_ready",
                "checks": checks,
            },
        )

    return {
        "status": "ready",
        "checks": checks,
    }