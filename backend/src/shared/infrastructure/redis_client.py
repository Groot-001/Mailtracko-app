from redis.asyncio import ConnectionPool, Redis

from src.core.config.settings import config

_pool: ConnectionPool | None = None


async def get_redis() -> Redis:
    global _pool
    if _pool is None:
        _pool = ConnectionPool.from_url(config.REDIS_URL, decode_responses=True)
    return Redis(connection_pool=_pool)


async def close_redis():
    global _pool
    if _pool:
        await _pool.disconnect()
        _pool = None
