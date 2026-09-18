import os
from collections.abc import AsyncGenerator

import redis.asyncio as aioredis

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

redis_pool = aioredis.ConnectionPool.from_url(REDIS_URL, decode_responses=True)

async def get_redis_client() -> AsyncGenerator[aioredis.Redis, None]:
    """Dependency for getting async redis client."""
    client = aioredis.Redis(connection_pool=redis_pool)
    try:
        yield client
    finally:
        await client.aclose()
