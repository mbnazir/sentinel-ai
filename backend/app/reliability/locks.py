from contextlib import asynccontextmanager
from redis.asyncio import Redis

@asynccontextmanager
async def distributed_lock(redis:Redis,key:str,ttl_seconds:int=900):
    token=await redis.set(key,"1",nx=True,ex=ttl_seconds)
    if not token:
        raise RuntimeError(f"lock already held: {key}")
    try:
        yield
    finally:
        await redis.delete(key)
