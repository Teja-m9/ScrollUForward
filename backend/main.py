"""
ScrollUForward — The Intelligence Platform
Main FastAPI application entry point.

3 AI Agents (Reel, Blog, News) → Validation Gate → Domain Router → Appwrite + S3
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from routes.auth_routes import router as auth_router
from routes.content_routes import router as content_router
from routes.discussion_routes import router as discussion_router
from routes.chat_routes import router as chat_router
from routes.user_routes import router as user_router
from routes.pipeline_routes import router as pipeline_router
from realtime import websocket_endpoint

# Configure logging for agents
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown events — schedule morning pipeline CRON."""
    logger = logging.getLogger("scrolluforward")
    logger.info("ScrollUForward API starting up — 3 agents ready")

    # Optional: Schedule daily pipeline at 5:00 AM UTC
    try:
        from apscheduler.schedulers.asyncio import AsyncIOScheduler
        from agents.orchestrator import run_full_pipeline

        scheduler = AsyncIOScheduler()
        scheduler.add_job(run_full_pipeline, "cron", hour=5, minute=0, id="morning_pipeline")
        scheduler.start()
        logger.info("Morning pipeline CRON scheduled (5:00 AM UTC daily)")
    except ImportError:
        logger.warning("APScheduler not installed — CRON disabled. Run pipeline manually via /pipeline/run")
    except Exception as e:
        logger.warning(f"CRON setup failed: {e} — Run pipeline manually via /pipeline/run")

    yield
    logger.info("ScrollUForward API shutting down")


app = FastAPI(
    title="ScrollUForward API",
    description="The Intelligence Platform — Where Curiosity Scales. 3 AI Agents, 12 Domain Pages.",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS — allow React Native / Expo connections
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
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
