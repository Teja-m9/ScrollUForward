"""AI Worker Service — port 8006
Handles async AI jobs: content generation, reel pipeline, bias analysis,
personalization scoring, and recommendation engine.
"""
from __future__ import annotations
import os, sys, json, asyncio, uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from enum import Enum

from fastapi import FastAPI, HTTPException, Header, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
from groq import Groq

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))
from microservices.shared.config import (
    APPWRITE_DATABASE_ID, COLLECTION_CONTENT, COLLECTION_USERS,
    GROQ_API_KEY, GROQ_MODEL_PRIMARY, GROQ_MODEL_FAST,
    DEEPGRAM_API_KEY, AWS_S3_BUCKET, AWS_REGION,
    AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY,
    QUALITY_SCORE_THRESHOLD,
)
from microservices.shared.appwrite_client import get_db
from microservices.shared.redis_client import (
    cache_get, cache_set, cache_delete_pattern,
    key_feed, key_ai_job,
)
from microservices.shared.auth import decode_token
from appwrite.id import ID
from appwrite.query import Query as AQ

# ── App ────────────────────────────────────────────────────────────────────
app = FastAPI(title="AI Worker Service", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

# In-memory job store (replace with Redis/Celery in production)
_jobs: Dict[str, dict] = {}

# ── Auth ───────────────────────────────────────────────────────────────────
async def current_user(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "Missing bearer token")
    payload = decode_token(authorization[7:])
    if not payload:
        raise HTTPException(401, "Invalid token")
    return payload

# ── Job status ─────────────────────────────────────────────────────────────
class JobStatus(str, Enum):
    PENDING   = "pending"
    RUNNING   = "running"
    COMPLETED = "completed"
    FAILED    = "failed"

def _new_job(job_type: str, params: dict) -> dict:
    job_id = str(uuid.uuid4())
    job = {
        "job_id": job_id,
        "type": job_type,
        "status": JobStatus.PENDING,
        "params": params,
        "result": None,
        "error": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    _jobs[job_id] = job
    return job

def _update_job(job_id: str, status: JobStatus, result=None, error=None):
    if job_id in _jobs:
        _jobs[job_id].update({
            "status": status,
            "result": result,
            "error": error,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        })

@app.get("/ai/jobs/{job_id}")
async def get_job(job_id: str):
    # Check Redis cache first
    cached = await cache_get(key_ai_job(job_id))
    if cached:
        return cached

    if job_id not in _jobs:
        raise HTTPException(404, "Job not found")
    return _jobs[job_id]

@app.get("/ai/jobs")
async def list_jobs(status: Optional[str] = None, limit: int = 20):
    jobs = list(_jobs.values())
    if status:
        jobs = [j for j in jobs if j["status"] == status]
    jobs.sort(key=lambda j: j["created_at"], reverse=True)
    return {"total": len(jobs), "jobs": jobs[:limit]}

# ── Schemas ────────────────────────────────────────────────────────────────
class ContentGenerationReq(BaseModel):
    topic: str
    domain: str = "technology"
    content_type: str = "article"  # article | reel_script | news_summary
    length: str = "medium"         # short | medium | long
    tone: str = "educational"      # educational | conversational | analytical
    user_id: Optional[str] = None

class BiasAnalysisReq(BaseModel):
    content_id: str
    text: str
    auto_flag: bool = True

class PersonalizationReq(BaseModel):
    user_id: str
    candidate_content_ids: List[str]
    top_n: int = 10

class TrendingReq(BaseModel):
    domain: Optional[str] = None
    hours: int = 24
    limit: int = 10

class SummaryReq(BaseModel):
    text: str
    max_sentences: int = 3

class QualityCheckReq(BaseModel):
    content_id: str
    title: str
    body: str

# ── Content Generation ─────────────────────────────────────────────────────
LENGTH_TOKENS = {"short": 300, "medium": 600, "long": 1200}
TONE_INSTRUCTIONS = {
    "educational": "Explain clearly with examples. Use structured paragraphs.",
    "conversational": "Write as if talking to a curious friend. Keep it engaging.",
    "analytical": "Provide deep analysis with multiple perspectives and data points.",
}

async def _run_content_generation(job_id: str, req: ContentGenerationReq):
    _update_job(job_id, JobStatus.RUNNING)
    if not groq_client:
        _update_job(job_id, JobStatus.FAILED, error="Groq not configured")
        return

    length_tokens = LENGTH_TOKENS.get(req.length, 600)
    tone_instr = TONE_INSTRUCTIONS.get(req.tone, TONE_INSTRUCTIONS["educational"])

    type_prompts = {
        "article": f"Write a {req.length} educational article about: {req.topic}",
        "reel_script": f"Write a short (60-90 second) narration script about: {req.topic}. No headers, just flowing narration.",
        "news_summary": f"Write a concise news summary about: {req.topic}. Include key facts and context.",
    }
    prompt = type_prompts.get(req.content_type, type_prompts["article"])

    try:
        resp = groq_client.chat.completions.create(
            model=GROQ_MODEL_PRIMARY,
            messages=[
                {"role": "system", "content": f"You are a {req.domain} content creator. {tone_instr}"},
                {"role": "user", "content": prompt},
            ],
            max_tokens=length_tokens,
            temperature=0.7,
        )
        generated = resp.choices[0].message.content.strip()
        result = {
            "topic": req.topic,
            "domain": req.domain,
            "content_type": req.content_type,
            "generated_text": generated,
            "word_count": len(generated.split()),
            "tokens_used": resp.usage.total_tokens,
        }
        _update_job(job_id, JobStatus.COMPLETED, result=result)
        await cache_set(key_ai_job(job_id), _jobs[job_id], 3600)
    except Exception as e:
        _update_job(job_id, JobStatus.FAILED, error=str(e))

@app.post("/ai/generate")
async def generate_content(req: ContentGenerationReq, bg: BackgroundTasks, user=Depends(current_user)):
    job = _new_job("content_generation", req.model_dump())
    bg.add_task(_run_content_generation, job["job_id"], req)
    return {"job_id": job["job_id"], "status": JobStatus.PENDING}

# ── Bias Analysis ──────────────────────────────────────────────────────────
BIAS_SYSTEM = (
    "You are a neutral bias detector. Analyze the text and return a JSON object with:\n"
    "- score: int 0-100 (0=no bias, 100=extreme bias)\n"
    "- flags: list of strings describing detected biases\n"
    "- verdict: one of 'clean', 'mild', 'moderate', 'severe'\n"
    "- explanation: one sentence explaining the verdict\n"
    "Return ONLY valid JSON."
)

async def _run_bias_analysis(job_id: str, req: BiasAnalysisReq):
    _update_job(job_id, JobStatus.RUNNING)
    if not groq_client:
        _update_job(job_id, JobStatus.FAILED, error="Groq not configured")
        return

    try:
        resp = groq_client.chat.completions.create(
            model=GROQ_MODEL_FAST,
            messages=[
                {"role": "system", "content": BIAS_SYSTEM},
                {"role": "user", "content": f"Text: {req.text[:4000]}"},  # cap at 4k chars
            ],
            max_tokens=300,
            temperature=0.1,
            response_format={"type": "json_object"},
        )
        result = json.loads(resp.choices[0].message.content)
        result["content_id"] = req.content_id

        # Auto-flag in Appwrite if score exceeds threshold
        if req.auto_flag and result.get("score", 0) >= QUALITY_SCORE_THRESHOLD:
            try:
                db = get_db()
                db.update_document(
                    APPWRITE_DATABASE_ID, COLLECTION_CONTENT, req.content_id,
                    {"bias_score": result["score"], "bias_flagged": True}
                )
            except Exception as e:
                print(f"[AI Worker] Failed to flag content {req.content_id}: {e}")

        _update_job(job_id, JobStatus.COMPLETED, result=result)
        await cache_set(key_ai_job(job_id), _jobs[job_id], 3600)
    except Exception as e:
        _update_job(job_id, JobStatus.FAILED, error=str(e))

@app.post("/ai/bias-check")
async def bias_check(req: BiasAnalysisReq, bg: BackgroundTasks):
    job = _new_job("bias_analysis", req.model_dump())
    bg.add_task(_run_bias_analysis, job["job_id"], req)
    return {"job_id": job["job_id"], "status": JobStatus.PENDING}

# ── Personalization ────────────────────────────────────────────────────────
async def _run_personalization(job_id: str, req: PersonalizationReq):
    _update_job(job_id, JobStatus.RUNNING)
    try:
        db = get_db()
        # Fetch user interest tags
        user_results = db.list_documents(
            APPWRITE_DATABASE_ID, COLLECTION_USERS,
            [AQ.equal("user_id", req.user_id), AQ.limit(1)]
        )
        if not user_results["documents"]:
            _update_job(job_id, JobStatus.FAILED, error="User not found")
            return

        user = user_results["documents"][0]
        interest_tags: List[str] = user.get("interest_tags", [])
        watched_domains: List[str] = user.get("watched_domains", [])

        scored = []
        for cid in req.candidate_content_ids:
            try:
                content = db.get_document(APPWRITE_DATABASE_ID, COLLECTION_CONTENT, cid)
                score = 0

                # Domain match
                if content.get("domain") in watched_domains:
                    score += 40

                # Tag overlap
                content_tags = content.get("tags", [])
                overlap = len(set(interest_tags) & set(content_tags))
                score += overlap * 10

                # Recency boost (newer = higher)
                created = content.get("$createdAt", "")
                if created:
                    age_hours = (datetime.now(timezone.utc) - datetime.fromisoformat(
                        created.replace("Z", "+00:00")
                    )).total_seconds() / 3600
                    score += max(0, 30 - int(age_hours / 4))  # decays over ~5 days

                # Engagement signal
                score += min(content.get("likes_count", 0), 20)
                score += min(content.get("views_count", 0) // 10, 10)

                scored.append({"content_id": cid, "score": score})
            except Exception:
                continue

        scored.sort(key=lambda x: x["score"], reverse=True)
        top = scored[: req.top_n]

        _update_job(job_id, JobStatus.COMPLETED, result={"ranked": top, "user_id": req.user_id})
        await cache_set(key_ai_job(job_id), _jobs[job_id], 600)
    except Exception as e:
        _update_job(job_id, JobStatus.FAILED, error=str(e))

@app.post("/ai/personalize")
async def personalize(req: PersonalizationReq, bg: BackgroundTasks):
    job = _new_job("personalization", req.model_dump())
    bg.add_task(_run_personalization, job["job_id"], req)
    return {"job_id": job["job_id"], "status": JobStatus.PENDING}

# ── Trending Detection ─────────────────────────────────────────────────────
@app.post("/ai/trending")
async def get_trending(req: TrendingReq):
    """Returns trending content based on interaction velocity."""
    db = get_db()
    queries = [AQ.order_desc("views_count"), AQ.limit(req.limit * 2)]
    if req.domain:
        queries.append(AQ.equal("domain", req.domain))

    results = db.list_documents(APPWRITE_DATABASE_ID, COLLECTION_CONTENT, queries)

    # Score by engagement velocity
    now = datetime.now(timezone.utc)
    trending = []
    for doc in results["documents"]:
        try:
            created = datetime.fromisoformat(doc.get("$createdAt", "").replace("Z", "+00:00"))
            age_hours = (now - created).total_seconds() / 3600
            if age_hours > req.hours:
                continue
            views = doc.get("views_count", 0)
            likes = doc.get("likes_count", 0)
            velocity = (views + likes * 3) / max(age_hours, 1)
            trending.append({
                "content_id": doc["$id"],
                "title": doc.get("title", ""),
                "domain": doc.get("domain", ""),
                "velocity": round(velocity, 2),
                "views": views,
                "likes": likes,
                "age_hours": round(age_hours, 1),
            })
        except Exception:
            continue

    trending.sort(key=lambda x: x["velocity"], reverse=True)
    return {"domain": req.domain, "hours": req.hours, "trending": trending[: req.limit]}

# ── Text Summarization ─────────────────────────────────────────────────────
@app.post("/ai/summarize")
async def summarize(req: SummaryReq):
    if not groq_client:
        raise HTTPException(503, "Groq not configured")

    try:
        resp = groq_client.chat.completions.create(
            model=GROQ_MODEL_FAST,
            messages=[
                {"role": "system", "content": f"Summarize the following text in exactly {req.max_sentences} sentences. Be concise and accurate."},
                {"role": "user", "content": req.text[:6000]},
            ],
            max_tokens=200,
            temperature=0.3,
        )
        return {"summary": resp.choices[0].message.content.strip()}
    except Exception as e:
        raise HTTPException(500, str(e))

# ── Quality Scoring ────────────────────────────────────────────────────────
QUALITY_SYSTEM = (
    "You are a content quality evaluator. Score the content on a scale 0-100 and return JSON:\n"
    "- score: int 0-100\n"
    "- issues: list of strings describing quality problems\n"
    "- verdict: one of 'excellent', 'good', 'fair', 'poor'\n"
    "- suggestions: list of 1-3 improvement suggestions\n"
    "Return ONLY valid JSON."
)

async def _run_quality_check(job_id: str, req: QualityCheckReq):
    _update_job(job_id, JobStatus.RUNNING)
    if not groq_client:
        _update_job(job_id, JobStatus.FAILED, error="Groq not configured")
        return

    try:
        resp = groq_client.chat.completions.create(
            model=GROQ_MODEL_FAST,
            messages=[
                {"role": "system", "content": QUALITY_SYSTEM},
                {"role": "user", "content": f"Title: {req.title}\n\nBody:\n{req.body[:3000]}"},
            ],
            max_tokens=300,
            temperature=0.1,
            response_format={"type": "json_object"},
        )
        result = json.loads(resp.choices[0].message.content)
        result["content_id"] = req.content_id

        # Update quality score in Appwrite
        try:
            db = get_db()
            db.update_document(
                APPWRITE_DATABASE_ID, COLLECTION_CONTENT, req.content_id,
                {"quality_score": result.get("score", 0)}
            )
        except Exception as e:
            print(f"[AI Worker] Quality score update failed: {e}")

        _update_job(job_id, JobStatus.COMPLETED, result=result)
        await cache_set(key_ai_job(job_id), _jobs[job_id], 3600)
    except Exception as e:
        _update_job(job_id, JobStatus.FAILED, error=str(e))

@app.post("/ai/quality-check")
async def quality_check(req: QualityCheckReq, bg: BackgroundTasks):
    job = _new_job("quality_check", req.model_dump())
    bg.add_task(_run_quality_check, job["job_id"], req)
    return {"job_id": job["job_id"], "status": JobStatus.PENDING}

# ── Tag Suggestion ─────────────────────────────────────────────────────────
class TagSuggestReq(BaseModel):
    title: str
    body: str
    domain: str = ""

@app.post("/ai/suggest-tags")
async def suggest_tags(req: TagSuggestReq):
    if not groq_client:
        raise HTTPException(503, "Groq not configured")

    try:
        resp = groq_client.chat.completions.create(
            model=GROQ_MODEL_FAST,
            messages=[
                {"role": "system", "content": "Extract 5-8 relevant topic tags from the content. Return ONLY a JSON array of lowercase strings. Example: [\"machine learning\", \"python\", \"neural networks\"]"},
                {"role": "user", "content": f"Domain: {req.domain}\nTitle: {req.title}\n\n{req.body[:1000]}"},
            ],
            max_tokens=150,
            temperature=0.2,
            response_format={"type": "json_object"},
        )
        # Handle both {"tags": [...]} and raw array responses
        raw = resp.choices[0].message.content.strip()
        parsed = json.loads(raw)
        tags = parsed if isinstance(parsed, list) else parsed.get("tags", [])
        return {"tags": tags[:8]}
    except Exception as e:
        raise HTTPException(500, str(e))

# ── Reel Script → Chapters ─────────────────────────────────────────────────
class ChapterReq(BaseModel):
    script: str
    target_duration_seconds: int = 60

@app.post("/ai/script-chapters")
async def script_to_chapters(req: ChapterReq):
    """Split a narration script into timed chapters for animation."""
    if not groq_client:
        raise HTTPException(503, "Groq not configured")

    words = req.script.split()
    # ~2.5 words/second speaking rate
    words_per_chapter = max(10, int(2.5 * req.target_duration_seconds / 5))
    chapters = []
    for i in range(0, len(words), words_per_chapter):
        chunk = " ".join(words[i: i + words_per_chapter])
        chapters.append({"index": len(chapters), "text": chunk, "word_count": len(chunk.split())})

    return {"total_chapters": len(chapters), "chapters": chapters}

# ── Health ─────────────────────────────────────────────────────────────────
@app.get("/ai/health")
async def health():
    return {
        "status": "ok",
        "service": "ai_worker",
        "port": 8006,
        "groq_configured": groq_client is not None,
        "active_jobs": len(_jobs),
        "pending_jobs": sum(1 for j in _jobs.values() if j["status"] == JobStatus.PENDING),
        "running_jobs": sum(1 for j in _jobs.values() if j["status"] == JobStatus.RUNNING),
    }
