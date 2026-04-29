import json
from app.core.config import settings
from app.integrations.redis_client import get_redis_client


class MappingStoreService:
    def _key(self, request_id: str) -> str:
        return f"sentinel:mapping:{request_id}"

    async def store_mapping(
        self,
        request_id: str,
        mappings: dict[str, str],
        entity_counts: dict[str, int],
    ) -> None:
        redis_client = get_redis_client()

        payload = {
            "request_id": request_id,
            "mappings": mappings,
            "entity_counts": entity_counts,
        }

        await redis_client.set(
            self._key(request_id),
            json.dumps(payload),
            ex=settings.REDIS_TTL_SECONDS,
        )

    async def get_mapping(self, request_id: str) -> dict[str, str]:
        redis_client = get_redis_client()

        raw = await redis_client.get(self._key(request_id))
        if not raw:
            return {}

        payload = json.loads(raw)
        return payload.get("mappings", {})

    async def delete_mapping(self, request_id: str) -> None:
        redis_client = get_redis_client()
        await redis_client.delete(self._key(request_id))