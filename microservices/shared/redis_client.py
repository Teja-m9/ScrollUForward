"""
Shared Redis client with helper methods for caching.
Used by: Content Service (feed cache), Discussion Service, Gateway (rate limiting).
"""
import json, logging
from typing import Any, Optional
import redis.asyncio as aioredis
from shared.config import REDIS_URL

log = logging.getLogger("redis_client")

_pool: Optional[aioredis.ConnectionPool] = None


def get_pool() -> aioredis.ConnectionPool:
    global _pool
    if _pool is None:
        _pool = aioredis.ConnectionPool.from_url(REDIS_URL, decode_responses=True)
    return _pool


def get_redis() -> aioredis.Redis:
    return aioredis.Redis(connection_pool=get_pool())


# ── Cache helpers ─────────────────────────────────────────────────────────────

async def cache_set(key: str, value: Any, ttl: int = 300) -> None:
    """Store JSON-serialisable value with TTL (seconds)."""
    r = get_redis()
    try:
        await r.set(key, json.dumps(value), ex=ttl)
    except Exception as e:
        log.warning(f"[Redis] set failed {key}: {e}")


async def cache_get(key: str) -> Optional[Any]:
    """Return cached value or None."""
    r = get_redis()
    try:
        raw = await r.get(key)
        return json.loads(raw) if raw else None
    except Exception as e:
        log.warning(f"[Redis] get failed {key}: {e}")
        return None


async def cache_delete(key: str) -> None:
    r = get_redis()
    try:
        await r.delete(key)
    except Exception as e:
        log.warning(f"[Redis] delete failed {key}: {e}")


async def cache_delete_pattern(pattern: str) -> None:
    """Delete all keys matching a pattern (e.g. 'feed:user:*')."""
    r = get_redis()
    try:
        keys = await r.keys(pattern)
        if keys:
            await r.delete(*keys)
    except Exception as e:
        log.warning(f"[Redis] delete_pattern failed {pattern}: {e}")


# ── Cache key builders ────────────────────────────────────────────────────────

def key_feed(user_id: str, page: int = 0) -> str:
    return f"feed:user:{user_id}:page:{page}"

def key_content(content_id: str) -> str:
    return f"content:{content_id}"

def key_user(user_id: str) -> str:
    return f"user:{user_id}"

def key_leaderboard() -> str:
    return "leaderboard:global"

def key_discussions(domain: str = "all") -> str:
    return f"discussions:{domain}"

def key_ai_job(job_id: str) -> str:
    return f"ai_job:{job_id}"

def key_rate_limit(ip: str, endpoint: str) -> str:
    return f"rate:{ip}:{endpoint}"
