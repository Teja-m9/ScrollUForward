"""
Shared slowapi limiter — imported by main.py (for app.state) and individual
route modules (for the @limiter.limit decorator).

Storage: backed by Redis when REDIS_URL is set, otherwise in-process memory
(fine for dev / single-instance, will under-count when running multiple
uvicorn workers without Redis).
"""
import os

from slowapi import Limiter
from slowapi.util import get_remote_address

REDIS_URL = os.getenv("REDIS_URL", "").strip()

# Storage URI choice:
# - In-memory: ~0 ms hot-path overhead, counters reset on restart, NOT shared
#   across instances. Fine for single-instance Railway.
# - Redis: durable + shared, but adds an Upstash round-trip (50–200 ms) to
#   EVERY rate-limited request. Slow when Upstash region is far.
# Default to memory for speed; flip RATE_LIMIT_STORAGE=redis to opt back in.
_use_redis = os.getenv("RATE_LIMIT_STORAGE", "memory").lower() == "redis"
storage_uri = REDIS_URL if (_use_redis and REDIS_URL) else "memory://"

limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=storage_uri,
    # NB: `headers_enabled=True` requires every rate-limited handler to declare a
    # `response: Response` parameter so slowapi can inject X-RateLimit-* headers.
    # Keeping it off — clients still get a clean 429 on overage.
    headers_enabled=False,
    default_limits=[],
)


def user_or_ip(request) -> str:
    """Key by authenticated user_id when present, otherwise client IP.

    The auth header is `Authorization: Bearer <jwt>` — we peek the sub claim
    without re-validating (limiter is best-effort, not a security boundary).
    """
    try:
        auth = request.headers.get("authorization") or request.headers.get("Authorization") or ""
        if auth.lower().startswith("bearer "):
            from auth import decode_token
            try:
                payload = decode_token(auth.split(None, 1)[1])
                uid = payload.get("sub")
                if uid:
                    return f"user:{uid}"
            except Exception:
                pass
    except Exception:
        pass
    return get_remote_address(request)
