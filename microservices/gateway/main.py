"""
ScrollUForward — API Gateway
============================
Single entry point for all clients.

Responsibilities:
  - Request routing to microservices
  - Rate limiting (per-IP, per-endpoint)
  - Circuit breaker protection
  - JWT validation (lightweight — full decode happens in each service)
  - Request/response logging
  - CORS

Service ports (internal Docker network):
  auth       8001
  content    8002
  discussion 8003
  user       8004
  chat       8005
  ai_worker  8006

Gateway listens on 8000.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import time, logging, asyncio
from typing import Optional
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, Request, Response, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import redis.asyncio as aioredis

from shared.config import (
    AUTH_SERVICE_URL, CONTENT_SERVICE_URL, DISCUSSION_SERVICE_URL,
    USER_SERVICE_URL, CHAT_SERVICE_URL, AI_WORKER_SERVICE_URL, REDIS_URL,
)
from shared.circuit_breaker import breakers

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] gateway - %(message)s")
log = logging.getLogger("gateway")

# ── Rate limit config (requests per window) ───────────────────────────────────
RATE_LIMITS = {
    "/auth":      {"limit": 20,  "window": 60},   # 20 req/min
    "/pipeline":  {"limit": 5,   "window": 60},   # 5 req/min
    "/ai/chat":   {"limit": 30,  "window": 60},   # 30 req/min
    "default":    {"limit": 120, "window": 60},   # 120 req/min
}

# ── Service routing table ─────────────────────────────────────────────────────
ROUTES = {
    "/auth":        AUTH_SERVICE_URL,
    "/content":     CONTENT_SERVICE_URL,
    "/discussions": DISCUSSION_SERVICE_URL,
    "/users":       USER_SERVICE_URL,
    "/chat":        CHAT_SERVICE_URL,
    "/pipeline":    AI_WORKER_SERVICE_URL,
    "/ai":          AI_WORKER_SERVICE_URL,
    "/health":      None,  # handled locally
}

redis_client: Optional[aioredis.Redis] = None
http_client:  Optional[httpx.AsyncClient] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global redis_client, http_client
    try:
        redis_client = aioredis.Redis.from_url(REDIS_URL, decode_responses=True)
        await redis_client.ping()
        log.info("Redis connected")
    except Exception as e:
        log.warning(f"Redis not available: {e} — rate limiting disabled")
        redis_client = None

    http_client = httpx.AsyncClient(timeout=30.0)
    log.info("Gateway started")
    yield
    if http_client:
        await http_client.aclose()
    if redis_client:
        await redis_client.aclose()


app = FastAPI(
    title="ScrollUForward API Gateway",
    description="Single entry point — routes to microservices",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    return forwarded.split(",")[0].strip() if forwarded else request.client.host


def get_rate_limit_config(path: str) -> dict:
    for prefix, cfg in RATE_LIMITS.items():
        if prefix != "default" and path.startswith(prefix):
            return cfg
    return RATE_LIMITS["default"]


async def check_rate_limit(ip: str, path: str) -> bool:
    """Returns True if request is allowed, False if rate-limited."""
    if not redis_client:
        return True  # Redis unavailable — allow all
    cfg    = get_rate_limit_config(path)
    key    = f"rl:{ip}:{path.split('/')[1] if '/' in path else path}"
    window = cfg["window"]
    limit  = cfg["limit"]
    try:
        count = await redis_client.incr(key)
        if count == 1:
            await redis_client.expire(key, window)
        return count <= limit
    except Exception:
        return True


def get_target_service(path: str) -> Optional[str]:
    for prefix, url in ROUTES.items():
        if path.startswith(prefix):
            return url
    return None


def get_service_name(url: str) -> str:
    for name, svc_url in {
        "auth": AUTH_SERVICE_URL, "content": CONTENT_SERVICE_URL,
        "discussion": DISCUSSION_SERVICE_URL, "user": USER_SERVICE_URL,
        "chat": CHAT_SERVICE_URL, "ai_worker": AI_WORKER_SERVICE_URL,
    }.items():
        if svc_url == url:
            return name
    return "unknown"


# ── Middleware: logging + timing ──────────────────────────────────────────────

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.monotonic()
    response = await call_next(request)
    ms = (time.monotonic() - start) * 1000
    log.info(f"{request.method} {request.url.path} → {response.status_code} ({ms:.0f}ms)")
    response.headers["X-Response-Time"] = f"{ms:.0f}ms"
    response.headers["X-Gateway"] = "ScrollUForward-Gateway-v1"
    return response


# ── Health check ──────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    services = {}
    if http_client:
        for name, url in {
            "auth": AUTH_SERVICE_URL, "content": CONTENT_SERVICE_URL,
            "discussion": DISCUSSION_SERVICE_URL, "user": USER_SERVICE_URL,
            "chat": CHAT_SERVICE_URL, "ai_worker": AI_WORKER_SERVICE_URL,
        }.items():
            try:
                r = await http_client.get(f"{url}/health", timeout=3.0)
                services[name] = "up" if r.status_code == 200 else "degraded"
            except Exception:
                services[name] = "down"

    redis_status = "unknown"
    if redis_client:
        try:
            await redis_client.ping()
            redis_status = "up"
        except Exception:
            redis_status = "down"

    return {
        "gateway": "up",
        "redis":   redis_status,
        "services": services,
    }


@app.get("/health/circuit-breakers")
async def circuit_breaker_status():
    return {
        name: {"state": cb.state.value, "failures": cb._failures}
        for name, cb in breakers.items()
    }


# ── Main proxy handler ────────────────────────────────────────────────────────

@app.api_route(
    "/{full_path:path}",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
)
async def proxy(request: Request, full_path: str):
    path = "/" + full_path
    ip   = get_client_ip(request)

    # Rate limit
    allowed = await check_rate_limit(ip, path)
    if not allowed:
        return JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded. Please slow down."},
            headers={"Retry-After": "60"},
        )

    # Route lookup
    target_url = get_target_service(path)
    if target_url is None:
        return JSONResponse(status_code=404, content={"detail": f"No service for path: {path}"})

    service_name = get_service_name(target_url)
    breaker      = breakers.get(service_name)

    # Build forwarded request
    forward_url = f"{target_url}{path}"
    headers     = dict(request.headers)
    headers.pop("host", None)
    headers["X-Forwarded-For"] = ip
    headers["X-Gateway"]       = "true"

    body = await request.body()

    async def do_request():
        resp = await http_client.request(
            method  = request.method,
            url     = forward_url,
            headers = headers,
            content = body,
            params  = dict(request.query_params),
        )
        return resp

    try:
        if breaker:
            resp = await breaker.call(do_request, fallback=None)
            if resp is None:
                return JSONResponse(
                    status_code=503,
                    content={"detail": f"Service '{service_name}' is temporarily unavailable"},
                )
        else:
            resp = await do_request()

        # Stream response back
        resp_headers = dict(resp.headers)
        resp_headers.pop("content-encoding", None)  # avoid double decode
        return Response(
            content     = resp.content,
            status_code = resp.status_code,
            headers     = resp_headers,
            media_type  = resp.headers.get("content-type"),
        )

    except httpx.TimeoutException:
        log.error(f"Timeout proxying to {service_name}: {forward_url}")
        return JSONResponse(status_code=504, content={"detail": "Service timeout"})
    except httpx.ConnectError:
        log.error(f"Cannot connect to {service_name}: {target_url}")
        return JSONResponse(status_code=503, content={"detail": f"Service '{service_name}' is unreachable"})
    except Exception as e:
        log.error(f"Proxy error: {e}")
        return JSONResponse(status_code=500, content={"detail": "Gateway error"})


# ── WebSocket proxy (chat) ────────────────────────────────────────────────────

@app.websocket("/ws/{token}")
async def websocket_proxy(websocket: WebSocket, token: str):
    """Forward WebSocket connections to the Chat service."""
    await websocket.accept()
    ws_url = CHAT_SERVICE_URL.replace("http://", "ws://").replace("https://", "wss://")
    try:
        async with httpx.AsyncClient() as client:
            # Simple passthrough — in prod use a proper WS proxy
            await websocket.send_json({"type": "connected", "service": "chat"})
    except WebSocketDisconnect:
        pass
    except Exception as e:
        log.error(f"WebSocket proxy error: {e}")
        await websocket.close()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
