import time

from fastapi import HTTPException, Request

from src.shared.infrastructure.redis_client import get_redis


def rate_limit(max_requests: int, window_seconds: int, key_prefix: str):
    async def dependency(request: Request) -> None:
        try:
            client_ip = request.client.host if request.client else "unknown"
            path = request.url.path
            key = f"rate_limit:{key_prefix}:{client_ip}:{path}"

            redis = await get_redis()
            now = time.time()
            window_start = now - window_seconds

            pipe = redis.pipeline()
            pipe.zremrangebyscore(key, 0, window_start)
            pipe.zcard(key)
            pipe.zadd(key, {str(now): now})
            pipe.expire(key, window_seconds)
            results = await pipe.execute()

            count = results[1]
            if count >= max_requests:
                raise HTTPException(
                    status_code=429,
                    detail="Too many requests. Please try again later.",
                )
        except HTTPException:
            raise
        except Exception:
            pass

    return dependency
