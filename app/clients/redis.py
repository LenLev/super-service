import os
from typing import Optional

from redis import asyncio as aioredis


class RedisClient:
    _instance: Optional[aioredis.Redis] = None

    @classmethod
    def get_client(cls) -> aioredis.Redis:
        if cls._instance is None:
            redis_host = os.getenv("REDIS_HOST", "localhost")
            redis_port = os.getenv("REDIS_PORT", "6379")
            redis_db = os.getenv("REDIS_DB", "1")
            redis_url = f"redis://{redis_host}:{redis_port}/{redis_db}"
            
            cls._instance = aioredis.from_url(redis_url, encoding="utf-8", decode_responses=True)
        return cls._instance

    @classmethod
    async def close(cls):
        if cls._instance:
            await cls._instance.close()
            cls._instance = None
