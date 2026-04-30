import logging
from datetime import datetime, timezone

from redis.exceptions import RedisError

from app.core.config import settings
from app.core.exceptions import MappingStoreError, RateLimitExceededError
from app.integrations.redis_client import get_redis_client

logger = logging.getLogger(__name__)


class RateLimitService:
    def _key(self, api_key_prefix: str) -> str:
        now = datetime.now(timezone.utc)
        bucket = int(now.timestamp() // settings.RATE_LIMIT_WINDOW_SECONDS)
        return f"sentinel:ratelimit:{api_key_prefix}:{bucket}"

    async def check_rate_limit(self, api_key_prefix: str) -> dict:
        redis_client = get_redis_client()
        key = self._key(api_key_prefix)

        try:
            current_count = await redis_client.incr(key)

            if current_count == 1:
                await redis_client.expire(
                    key,
                    settings.RATE_LIMIT_WINDOW_SECONDS,
                )

            ttl = await redis_client.ttl(key)

        except RedisError as exc:
            logger.exception("Failed to check rate limit in Redis.")
            raise MappingStoreError("Rate limit store is unavailable.") from exc

        allowed = current_count <= settings.RATE_LIMIT_REQUESTS

        result = {
            "limit": settings.RATE_LIMIT_REQUESTS,
            "window_seconds": settings.RATE_LIMIT_WINDOW_SECONDS,
            "used": int(current_count),
            "remaining": max(settings.RATE_LIMIT_REQUESTS - int(current_count), 0),
            "reset_seconds": max(int(ttl), 0),
        }

        if not allowed:
            raise RateLimitExceededError("Rate limit exceeded.")

        return result