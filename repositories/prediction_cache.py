from typing import Any, Optional
import json

from redis.asyncio import Redis


class PredictionCacheRepository:
    TTL_SECONDS = 3600

    def __init__(self, redis_client: Redis) -> None:
        self._redis = redis_client

    async def get_prediction(self, item_id: int) -> Optional[dict[str, Any]]:
        key = self._get_key(item_id)
        data = await self._redis.get(key)
        if data:
            return json.loads(data)
        return None

    async def set_prediction(self, item_id: int, prediction: dict[str, Any]) -> None:
        key = self._get_key(item_id)
        await self._redis.set(key, json.dumps(prediction, default=str), ex=self.TTL_SECONDS)

    async def delete_prediction(self, item_id: int) -> None:
        key = self._get_key(item_id)
        await self._redis.delete(key)

    def _get_key(self, item_id: int) -> str:
        return f"prediction:{item_id}"
