"""
Pipeline API Routes — trigger agents, check status, manage the morning publish pipeline.
"""
import asyncio
import logging
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query as QueryParam, BackgroundTasks
from pydantic import BaseModel
from typing import Optional

from agents.orchestrator import run_full_pipeline, run_single_agent, get_todays_domains
from config import DOMAINS, GROQ_API_KEY

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/pipeline", tags=["Pipeline"])

# Track pipeline runs in memory
_pipeline_runs: dict[str, dict] = {}


class PipelineTriggerRequest(BaseModel):
    domains: Optional[list[str]] = None


class SingleAgentRequest(BaseModel):
    agent_type: str  # reel, blog, news
    domain: str = "technology"


# ── Health / Config Check ─────────────────────────────────
@router.get("/status")
async def pipeline_status():
    """Check if the pipeline is configured and ready to run."""
    keys_configured = {
        "groq": bool(GROQ_API_KEY),
        "google_ai": bool(__import__("config").GOOGLE_AI_API_KEY),
        "elevenlabs": bool(__import__("config").ELEVENLABS_API_KEY),
        "aws_s3": bool(__import__("config").AWS_ACCESS_KEY_ID),
        "serpapi": bool(__import__("config").SERPAPI_KEY),
        "newsapi": bool(__import__("config").NEWSAPI_KEY),
    }
    all_critical = keys_configured["groq"]  # Groq is the only truly required key

    return {
        "status": "ready" if all_critical else "missing_keys",
        "keys_configured": keys_configured,
        "todays_domains": get_todays_domains(),
        "available_domains": DOMAINS,
        "recent_runs": list(_pipeline_runs.values())[-5:],
    }


# ── Full Pipeline ─────────────────────────────────────────
@router.post("/run")
async def trigger_full_pipeline(
    req: PipelineTriggerRequest,
    background_tasks: BackgroundTasks,
):
    """
    Trigger the full morning pipeline.
    Runs all 3 agents in parallel → validation → publish.
    """
    if not GROQ_API_KEY:
        raise HTTPException(status_code=503, detail="GROQ_API_KEY not configured")

    run_id = f"run_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
    domains = req.domains or get_todays_domains()

    # Validate domains
    for d in domains:
        if d not in DOMAINS:
            raise HTTPException(status_code=400, detail=f"Invalid domain: {d}")

    _pipeline_runs[run_id] = {
        "run_id": run_id,
        "status": "running",
        "started_at": datetime.utcnow().isoformat(),
        "domains": domains,
    }

    async def _run():
        try:
            result = await run_full_pipeline(domains)
            _pipeline_runs[run_id].update(result)
            _pipeline_runs[run_id]["status"] = "completed"
        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            _pipeline_runs[run_id]["status"] = "failed"
            _pipeline_runs[run_id]["error"] = str(e)

    background_tasks.add_task(asyncio.ensure_future, _run())

    return {
        "run_id": run_id,
        "status": "started",
        "domains": domains,
        "message": "Pipeline started in background. Check /pipeline/run/{run_id} for status.",
    }


@router.get("/run/{run_id}")
async def get_pipeline_run(run_id: str):
    """Check the status of a pipeline run."""
    if run_id not in _pipeline_runs:
        raise HTTPException(status_code=404, detail="Pipeline run not found")
    return _pipeline_runs[run_id]


# ── Single Agent ──────────────────────────────────────────
@router.post("/agent")
async def trigger_single_agent(req: SingleAgentRequest):
    """
    Trigger a single agent (reel, blog, or news) for testing.
    Runs synchronously and returns the result.
    """
    if not GROQ_API_KEY:
        raise HTTPException(status_code=503, detail="GROQ_API_KEY not configured")

    if req.agent_type not in ["reel", "blog", "news"]:
        raise HTTPException(status_code=400, detail="agent_type must be reel, blog, or news")

    if req.domain not in DOMAINS:
        raise HTTPException(status_code=400, detail=f"Invalid domain: {req.domain}")

    try:
        result = await run_single_agent(req.agent_type, req.domain)
        return result
    except Exception as e:
        logger.error(f"Agent {req.agent_type} failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── Today's Domains ───────────────────────────────────────
@router.get("/domains/today")
async def todays_domains():
    """Get today's domain rotation."""
    return {
        "date": datetime.utcnow().strftime("%Y-%m-%d"),
        "domains": get_todays_domains(),
        "all_domains": DOMAINS,
    }
