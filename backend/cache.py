"""
Redis cache layer.

Two-tier:
  L1 = in-process dict (microseconds, not shared across instances)
  L2 = Redis (Upstash) — shared, durable, slower if region is far

Read path: L1 → L2 → origin. Writes go to both.
L1 default TTL = min(stage_ttl, 10s) so it doesn't drift far from L2.

Fail-open by design: if `REDIS_URL` is unset OR Redis is unreachable, every
helper degrades to a no-op (cache miss). The app must keep working without
the cache, just slower.
"""
import asyncio
import functools
import hashlib
import json
import logging
import os
import time
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)

# Toggle flag — defaults true, set CACHE_ENABLED=0 to disable globally
CACHE_ENABLED = os.getenv("CACHE_ENABLED", "1") not in ("0", "false", "False")
REDIS_URL = os.getenv("REDIS_URL", "").strip()

# L1 in-process cache: { key: (value, expires_at_epoch) }
_L1: dict[str, tuple[Any, float]] = {}
L1_MAX_TTL = float(os.getenv("L1_MAX_TTL", "30"))     # cap L1 freshness at 30s
L1_MAX_ENTRIES = int(os.getenv("L1_MAX_ENTRIES", "2000"))

# Counters surfaced via Stage 5's /metrics endpoint
_cache_hits = 0
_cache_misses = 0


def _l1_get(key: str) -> Optional[Any]:
    entry = _L1.get(key)
    if entry is None:
        return None
    value, expires_at = entry
    if time.time() >= expires_at:
        _L1.pop(key, None)
        return None
    return value


def _l1_set(key: str, value: Any, ttl: int):
    if len(_L1) >= L1_MAX_ENTRIES:
        # Evict oldest 10% — cheap LRU-ish without locking
        cutoff = sorted(_L1.values(), key=lambda v: v[1])[:L1_MAX_ENTRIES // 10]
        cutoff_set = {id(v) for v in cutoff}
        for k in list(_L1.keys()):
            if id(_L1[k]) in cutoff_set:
                _L1.pop(k, None)
    _L1[key] = (value, time.time() + min(ttl, L1_MAX_TTL))


def _l1_invalidate(*patterns: str):
    """Wildcard-free pattern match: any key containing the pattern is dropped."""
    for pattern in patterns:
        for k in list(_L1.keys()):
            if pattern == k or (pattern.endswith("*") and k.startswith(pattern[:-1])):
                _L1.pop(k, None)


def _is_active() -> bool:
    return CACHE_ENABLED and bool(REDIS_URL)


# ── Lazy async client singleton ──────────────────────────
_client = None
_client_lock = asyncio.Lock()


async def get_redis():
    """Return a shared async Redis client, or None if cache is disabled / unreachable."""
    global _client
    if not _is_active():
        return None
    if _client is not None:
        return _client
    async with _client_lock:
        if _client is None:
            try:
                # Local import so the module is safe to load even when redis isn't installed
                from redis.asyncio import Redis
                _client = Redis.from_url(
                    REDIS_URL,
                    decode_responses=True,
                    socket_connect_timeout=3,
                    socket_timeout=3,
                    retry_on_timeout=False,
                    health_check_interval=30,
                )
                # Verify connectivity once
                await _client.ping()
                logger.info("Redis cache layer connected")
            except Exception as e:
                logger.warning(f"Redis unavailable, cache disabled: {e}")
                _client = None
    return _client


async def close_redis():
    global _client
    if _client is not None:
        try:
            await _client.aclose()
        except Exception:
            pass
        _client = None


# ── Hit/miss counters (read by /metrics) ──────────────────
def cache_hit_count() -> int:
    return _cache_hits


def cache_miss_count() -> int:
    return _cache_misses


# ── Public helpers ───────────────────────────────────────
async def cache_get(key: str) -> Optional[str]:
    """Return the cached string value or None on miss/error."""
    global _cache_hits, _cache_misses
    r = await get_redis()
    if r is None:
        _cache_misses += 1
        return None
    try:
        val = await r.get(key)
        if val is None:
            _cache_misses += 1
            return None
        _cache_hits += 1
        return val
    except Exception as e:
        logger.warning(f"cache_get({key}) failed: {e}")
        _cache_misses += 1
        return None


async def cache_get_json(key: str) -> Optional[Any]:
    # L1 first — microsecond hit, no network
    l1 = _l1_get(key)
    if l1 is not None:
        global _cache_hits
        _cache_hits += 1
        return l1
    # L2 (Redis)
    raw = await cache_get(key)
    if raw is None:
        return None
    try:
        value = json.loads(raw)
        _l1_set(key, value, ttl=int(L1_MAX_TTL))
        return value
    except Exception:
        return None


def _to_jsonable(value: Any) -> Any:
    """Recursively convert Pydantic models, sets, etc. into JSON-friendly types."""
    if hasattr(value, "model_dump"):           # Pydantic v2
        return value.model_dump(mode="json")
    if hasattr(value, "dict") and callable(getattr(value, "dict")):
        try:
            return value.dict()                # Pydantic v1
        except Exception:
            pass
    if isinstance(value, list):
        return [_to_jsonable(v) for v in value]
    if isinstance(value, tuple):
        return [_to_jsonable(v) for v in value]
    if isinstance(value, set):
        return [_to_jsonable(v) for v in value]
    if isinstance(value, dict):
        return {k: _to_jsonable(v) for k, v in value.items()}
    return value


async def cache_set_json(key: str, value: Any, ttl: int = 60) -> bool:
    """Store JSON-serialised value with TTL in both L1 (in-process) and L2 (Redis)."""
    normalised = _to_jsonable(value)

    # Always write L1 — microsecond cost, big win on next read
    try:
        _l1_set(key, normalised, ttl=ttl)
    except Exception:
        pass

    r = await get_redis()
    if r is None:
        return True   # L1-only write still counts as success
    try:
        await r.set(key, json.dumps(normalised, default=str), ex=ttl)
        return True
    except Exception as e:
        logger.warning(f"cache_set_json({key}) failed: {e}")
        return False


async def cache_delete(*keys: str) -> int:
    if not keys:
        return 0
    r = await get_redis()
    if r is None:
        return 0
    try:
        return int(await r.delete(*keys))
    except Exception as e:
        logger.warning(f"cache_delete failed: {e}")
        return 0


async def cache_invalidate(*patterns: str) -> int:
    """Delete every key matching any of the glob patterns from both L1 + L2."""
    # L1 first
    _l1_invalidate(*patterns)

    r = await get_redis()
    if r is None:
        return 0
    deleted = 0
    try:
        for pattern in patterns:
            cursor = 0
            while True:
                cursor, batch = await r.scan(cursor=cursor, match=pattern, count=200)
                if batch:
                    deleted += int(await r.delete(*batch))
                if cursor == 0:
                    break
    except Exception as e:
        logger.warning(f"cache_invalidate({patterns}) failed: {e}")
    return deleted


# ── Decorator: @cached(ttl, key_fn=lambda *a, **kw: "...") ──
def cached(ttl: int = 60, key_fn: Optional[Callable[..., str]] = None, prefix: str = ""):
    """
    Cache the JSON-serialisable return value of an async function in Redis.

    Usage:
        @cached(ttl=30, key_fn=lambda user_id: f"user:{user_id}:stats")
        async def get_user_stats(user_id: str): ...

    If `key_fn` is None, derives a stable key from a hash of the args.
    """
    def decorator(fn):
        @functools.wraps(fn)
        async def wrapped(*args, **kwargs):
            if not _is_active():
                return await fn(*args, **kwargs)

            try:
                if key_fn is not None:
                    key = key_fn(*args, **kwargs)
                else:
                    raw = json.dumps([args, kwargs], default=str, sort_keys=True)
                    key = hashlib.sha1(raw.encode()).hexdigest()
                if prefix:
                    key = f"{prefix}:{key}"
            except Exception:
                # If we can't compute the key, just call through
                return await fn(*args, **kwargs)

            cached_val = await cache_get_json(key)
            if cached_val is not None:
                return cached_val

            result = await fn(*args, **kwargs)
            # Don't cache None / errors
            if result is not None:
                await cache_set_json(key, result, ttl=ttl)
            return result
        return wrapped
    return decorator


# ── Distributed lock (Stage 1: replaces in-memory asyncio.Lock for queue ops) ──
class RedisLock:
    """Tiny SETNX-based distributed lock with TTL.

    Usage:
        async with RedisLock("battle:queue", ttl=5):
            ...
    """
    def __init__(self, name: str, ttl: int = 5):
        self.name = f"lock:{name}"
        self.ttl = ttl
        self._token: Optional[str] = None

    async def __aenter__(self):
        r = await get_redis()
        if r is None:
            return self  # no-op when cache disabled
        # Spin up to ttl seconds for the lock
        token = os.urandom(8).hex()
        deadline = asyncio.get_event_loop().time() + self.ttl
        while True:
            ok = await r.set(self.name, token, ex=self.ttl, nx=True)
            if ok:
                self._token = token
                return self
            if asyncio.get_event_loop().time() >= deadline:
                # Couldn't acquire — proceed without (degraded, not blocking)
                return self
            await asyncio.sleep(0.05)

    async def __aexit__(self, *exc):
        if self._token is None:
            return
        r = await get_redis()
        if r is None:
            return
        try:
            # Only delete if the token still matches (don't delete someone else's lock)
            current = await r.get(self.name)
            if current == self._token:
                await r.delete(self.name)
        except Exception:
            pass
