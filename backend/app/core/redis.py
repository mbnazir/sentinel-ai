from redis.asyncio import Redis

from app.core.config import settings

redis_client = Redis.from_url(settings.redis_url, decode_responses=True)


async def redis_healthcheck() -> bool:
    try:
        return bool(await redis_client.ping())
    except Exception:
        return False


async def close_redis() -> None:
    await redis_client.aclose()
