import redis.asyncio as redis

from . import config

_client: redis.Redis | None = None


def init() -> None:
    global _client
    _client = redis.from_url(config.REDIS_URL, decode_responses=True)


async def get(code: str) -> str | None:
    try:
        return await _client.get(f"link:{code}")
    except Exception:
        return None  # кеш не критичен


async def set(code: str, url: str) -> None:
    try:
        await _client.set(f"link:{code}", url, ex=config.CACHE_TTL)
    except Exception:
        pass


async def close() -> None:
    if _client:
        await _client.aclose()
