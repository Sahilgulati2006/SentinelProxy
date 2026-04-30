import logging
from datetime import datetime, timezone

from redis.exceptions import RedisError

from app.core.exceptions import MappingStoreError
from app.integrations.redis_client import get_redis_client

logger = logging.getLogger(__name__)


class BudgetExceededError(Exception):
    """Raised when a user exceeds their monthly token budget."""


class BudgetService:
    def _usage_key(self, user_id: str) -> str:
        now = datetime.now(timezone.utc)
        return f"sentinel:usage:{user_id}:{now.year}:{now.month:02d}"

    async def get_usage(self, user_id: str) -> int:
        redis_client = get_redis_client()

        try:
            value = await redis_client.get(self._usage_key(user_id))
        except RedisError as exc:
            logger.exception("Failed to read usage from Redis.")
            raise MappingStoreError("Usage store is unavailable.") from exc

        return int(value or 0)

    async def check_budget(
        self,
        user_id: str,
        monthly_token_limit: int,
    ) -> dict:
        used_tokens = await self.get_usage(user_id)
        remaining_tokens = max(monthly_token_limit - used_tokens, 0)

        if used_tokens >= monthly_token_limit:
            raise BudgetExceededError("Monthly token budget exceeded.")

        return {
            "monthly_token_limit": monthly_token_limit,
            "used_tokens": used_tokens,
            "remaining_tokens": remaining_tokens,
        }

    async def increment_usage(
        self,
        user_id: str,
        monthly_token_limit: int,
        tokens: int,
    ) -> dict:
        redis_client = get_redis_client()
        key = self._usage_key(user_id)

        try:
            new_total = await redis_client.incrby(key, tokens)
        except RedisError as exc:
            logger.exception("Failed to increment usage in Redis.")
            raise MappingStoreError("Usage store is unavailable.") from exc

        return {
            "monthly_token_limit": monthly_token_limit,
            "used_tokens": int(new_total),
            "remaining_tokens": max(monthly_token_limit - int(new_total), 0),
        }