import json
import logging

from redis.exceptions import RedisError

from app.core.config import settings
from app.core.exceptions import MappingStoreError
from app.integrations.redis_client import get_redis_client

logger = logging.getLogger(__name__)


class MappingStoreService:
    def _key(self, request_id: str) -> str:
        return f"sentinel:mapping:{request_id}"

    async def store_mapping(
        self,
        request_id: str,
        mappings: dict[str, str],
        entity_counts: dict[str, int],
    ) -> None:
        if not mappings:
            return

        redis_client = get_redis_client()

        payload = {
            "request_id": request_id,
            "mappings": mappings,
            "entity_counts": entity_counts,
        }

        try:
            await redis_client.set(
                self._key(request_id),
                json.dumps(payload),
                ex=settings.REDIS_TTL_SECONDS,
            )
        except RedisError as exc:
            logger.exception("Failed to store redaction mapping in Redis.")
            raise MappingStoreError(
                "Secure mapping store is unavailable."
            ) from exc

    async def get_mapping(self, request_id: str) -> dict[str, str]:
        redis_client = get_redis_client()

        try:
            raw = await redis_client.get(self._key(request_id))
        except RedisError as exc:
            logger.exception("Failed to retrieve redaction mapping from Redis.")
            raise MappingStoreError(
                "Secure mapping store is unavailable."
            ) from exc

        if not raw:
            return {}

        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            logger.exception("Stored mapping payload is invalid JSON.")
            raise MappingStoreError(
                "Secure mapping payload is corrupted."
            ) from exc

        return payload.get("mappings", {})

    async def delete_mapping(self, request_id: str) -> None:
        redis_client = get_redis_client()

        try:
            await redis_client.delete(self._key(request_id))
        except RedisError:
            logger.warning(
                "Failed to delete redaction mapping from Redis.",
                exc_info=True,
            )