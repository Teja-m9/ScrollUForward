"""
ScrollUForward — The Intelligence Platform
Main FastAPI application entry point.

3 AI Agents (Reel, Blog, News) → Validation Gate → Domain Router → Appwrite + S3
"""
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse

from routes.auth_routes import router as auth_router
from routes.content_routes import router as content_router
from routes.discussion_routes import router as discussion_router
from routes.chat_routes import router as chat_router
from routes.user_routes import router as user_router
from routes.pipeline_routes import router as pipeline_router
from routes.admin_routes import router as admin_router
from routes.quiz_routes import router as quiz_router
from routes.flashcard_routes import router as flashcard_router
from routes.map_routes import router as map_router
from routes.brain_routes import router as brain_router
from routes.battle_routes import router as battle_router
from routes.metrics_routes import router as metrics_router, HTTP_REQUESTS, HTTP_DURATION
from realtime import websocket_endpoint
from cache import get_redis, close_redis

# Configure logging for agents
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("scrolluforward")


# ─── Sentry (Stage 5) ──────────────────────────────────────
SENTRY_DSN = os.getenv("SENTRY_DSN", "").strip()
if SENTRY_DSN:
    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.starlette import StarletteIntegration

        sentry_sdk.init(
            dsn=SENTRY_DSN,
            environment=os.getenv("ENV", "local"),
            traces_sample_rate=float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.1")),
            profiles_sample_rate=float(os.getenv("SENTRY_PROFILES_SAMPLE_RATE", "0.1")),
            integrations=[FastApiIntegration(), StarletteIntegration()],
            send_default_pii=False,
        )
        logger.info("Sentry error tracking enabled")
    except Exception as e:
        logger.warning(f"Sentry init failed: {e}")


# ─── Slowapi rate limiter (Stage 1) ─────────────────────────
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from rate_limit import limiter

REDIS_URL = os.getenv("REDIS_URL", "").strip()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown — Redis pool, daily CRON pipeline."""
    logger.info("ScrollUForward API starting up — 3 agents ready")

    # Touch the Redis pool early so we know if it's reachable
    if REDIS_URL:
        await get_redis()

    # Daily AI pipeline at 5am UTC (kept on APScheduler until Stage 4 ARQ replaces it)
    try:
        from apscheduler.schedulers.asyncio import AsyncIOScheduler
        from agents.orchestrator import run_full_pipeline

        scheduler = AsyncIOScheduler()
        scheduler.add_job(run_full_pipeline, "cron", hour=5, minute=0, id="morning_pipeline")
        scheduler.start()
        logger.info("Morning pipeline CRON scheduled (5:00 AM UTC daily)")
    except ImportError:
        logger.warning("APScheduler not installed — CRON disabled.")
    except Exception as e:
        logger.warning(f"CRON setup failed: {e}")

    yield

    await close_redis()
    logger.info("ScrollUForward API shutting down")


app = FastAPI(
    title="ScrollUForward API",
    description="The Intelligence Platform — Where Curiosity Scales. 3 AI Agents, 12 Domain Pages.",
    version="2.0.0",
    lifespan=lifespan,
)

# Hook the slowapi rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Response compression — minimum 1 KB, ratio is huge for JSON
app.add_middleware(GZipMiddleware, minimum_size=1024)

# ─── CORS — Stage 1 hardening ─────────────────────────────
def _parse_origins() -> list[str]:
    raw = os.getenv("ALLOWED_ORIGINS", "").strip()
    if raw:
        return [o.strip() for o in raw.split(",") if o.strip()]
    # Sensible defaults for dev
    return [
        "http://localhost:8081",
        "http://192.168.1.46:8081",
        "exp://192.168.1.46:8081",
        "scrolluforward://*",
        "*",   # last-resort wildcard until production origins are pinned
    ]


_allow_origins = _parse_origins()
_allow_origin_regex = None
if "*" in _allow_origins:
    # Wildcard fallback — keep credentials disabled to comply with browser policy
    _allow_credentials = False
else:
    _allow_credentials = True

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allow_origins,
    allow_origin_regex=_allow_origin_regex,
    allow_credentials=_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routers
app.include_router(auth_router)
app.include_router(content_router)
app.include_router(discussion_router)
app.include_router(chat_router)
app.include_router(user_router)
app.include_router(pipeline_router)
app.include_router(admin_router)
app.include_router(quiz_router)
app.include_router(flashcard_router)
app.include_router(map_router)
app.include_router(brain_router)
app.include_router(battle_router)
app.include_router(metrics_router)


# ─── Request duration middleware (Stage 5 metrics) ─────────
@app.middleware("http")
async def _metrics_middleware(request: Request, call_next):
    import time as _time
    start = _time.perf_counter()
    response = await call_next(request)
    duration = _time.perf_counter() - start
    try:
        path = request.url.path
        # Don't pollute metrics with high-cardinality paths
        if any(seg in path for seg in ("/static/", "/favicon", "/openapi", "/docs")):
            return response
        HTTP_REQUESTS.labels(
            method=request.method,
            path=path,
            status=str(response.status_code),
        ).inc()
        HTTP_DURATION.labels(method=request.method, path=path).observe(duration)
    except Exception:
        pass
    return response


# WebSocket endpoint for real-time chat
@app.websocket("/ws/{token}")
async def ws_endpoint(websocket: WebSocket, token: str):
    await websocket_endpoint(websocket, token)


@app.get("/")
async def root():
    return {
        "name": "ScrollUForward API",
        "version": "2.0.0",
        "tagline": "Where Curiosity Scales",
        "status": "running",
        "agents": ["Reel Agent", "Blog Agent", "News Agent"],
        "endpoints": {
            "auth": "/auth",
            "content": "/content",
            "discussions": "/discussions",
            "chat": "/chat",
            "users": "/users",
            "pipeline": "/pipeline",
            "websocket": "/ws/{token}",
            "docs": "/docs",
        },
    }


@app.get("/health")
async def health():
    return {"status": "healthy", "agents": 3, "domains": 12}
