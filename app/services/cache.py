import redis.asyncio as aioredis
import json
import asyncio
from typing import Optional, Callable, Any
from app.core.config import settings

_redis: Optional[aioredis.Redis] = None
_locks: dict = {}

async def get_redis() -> aioredis.Redis:
    global _redis
    if _redis is None:
        _redis = aioredis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            max_connections=20,
        )
    return _redis

async def cache_get(key: str) -> Optional[dict]:
    r = await get_redis()
    val = await r.get(key)
    return json.loads(val) if val else None

async def cache_set(key: str, value: Any, ttl: int = 300) -> None:
    r = await get_redis()
    await r.setex(key, ttl, json.dumps(value))

async def cache_delete(key: str) -> None:
    r = await get_redis()
    await r.delete(key)

async def get_or_compute(key: str, compute_fn: Callable, ttl: int = 300) -> tuple[Any, bool]:
    # Cache stampede protection logic ikkade untundi
    cached = await cache_get(key)
    if cached is not None:
        return cached, True

    if key not in _locks:
        _locks[key] = asyncio.Lock()

    async with _locks[key]:
        cached = await cache_get(key)
        if cached is not None:
            return cached, True

        value = await compute_fn()
        await cache_set(key, value, ttl)
        _locks.pop(key, None)
        return value, False