"""
Prometheus metrics endpoint — Stage 5 of the scale-out plan.

Scrape with:
    curl -H "X-Metrics-Token: $METRICS_TOKEN" /metrics

The route is gated by METRICS_TOKEN (random secret env var) so bots can't
enumerate metrics. Empty token = wide open (only OK for local dev).
"""
import os
import time
from fastapi import APIRouter, Request, HTTPException, Response
from prometheus_client import (
    Counter, Gauge, Histogram, generate_latest, CONTENT_TYPE_LATEST,
)

router = APIRouter(tags=["Observability"])

METRICS_TOKEN = os.getenv("METRICS_TOKEN", "").strip()

# ─── Metrics ──────────────────────────────────────────────
HTTP_REQUESTS = Counter(
    "http_requests_total",
    "Number of HTTP requests served",
    ["method", "path", "status"],
)
HTTP_DURATION = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "path"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)
CACHE_HITS = Counter("cache_hits_total", "Number of cache hits")
CACHE_MISSES = Counter("cache_misses_total", "Number of cache misses")
WS_CONNECTIONS = Gauge("ws_active_connections", "Active WebSocket connections (this process)")
ARQ_QUEUE_DEPTH = Gauge("arq_queue_depth", "Pending ARQ jobs in the default queue")


@router.get("/metrics")
async def metrics(request: Request):
    """Prometheus scrape endpoint. Token-gated."""
    if METRICS_TOKEN:
        supplied = request.headers.get("x-metrics-token", "").strip()
        if supplied != METRICS_TOKEN:
            raise HTTPException(status_code=401, detail="metrics token required")

    # Pull live counts from the cache module on each scrape
    try:
        import cache as _cache
        # cache_hits / cache_misses are already Prometheus counters via this
        # module; the cache module also keeps independent integer counters
        # we sync from. Latch any new hits/misses since last scrape.
        # We use a simple monotonic-diff trick stored in module-level vars.
        prev_hits = getattr(metrics, "_prev_hits", 0)
        prev_misses = getattr(metrics, "_prev_misses", 0)
        cur_hits = _cache.cache_hit_count()
        cur_misses = _cache.cache_miss_count()
        if cur_hits > prev_hits:
            CACHE_HITS.inc(cur_hits - prev_hits)
        if cur_misses > prev_misses:
            CACHE_MISSES.inc(cur_misses - prev_misses)
        metrics._prev_hits = cur_hits
        metrics._prev_misses = cur_misses
    except Exception:
        pass

    # Per-process WS count
    try:
        from realtime import manager
        WS_CONNECTIONS.set(sum(len(v) for v in manager.active_connections.values()))
    except Exception:
        pass

    # ARQ queue depth (best-effort — only meaningful when REDIS_URL is set)
    try:
        from cache import get_redis
        r = await get_redis()
        if r is not None:
            depth = await r.llen("arq:queue")
            ARQ_QUEUE_DEPTH.set(int(depth or 0))
    except Exception:
        pass

    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
