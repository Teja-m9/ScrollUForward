"""
ARQ background worker — Stage 4 of the scale-out plan.

Run alongside the FastAPI web process:

    arq worker.WorkerSettings

Tasks:
  • generate_quiz_pool(domain)      — every 6h per domain, fills Redis quiz:pool:{domain}
  • refresh_trending_aggregate()    — every 60s, refreshes Redis trending:24h
  • run_daily_pipeline()            — 05:00 UTC, replaces APScheduler

When `REDIS_URL` is unset the worker exits — there's no broker to talk to.
"""
import asyncio
import json
import logging
import os
import time
from datetime import datetime, timedelta

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [worker:%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("worker")


# ─── Sentry on the worker side too (Stage 5) ──────────────
SENTRY_DSN = os.getenv("SENTRY_DSN", "").strip()
if SENTRY_DSN:
    try:
        import sentry_sdk
        sentry_sdk.init(
            dsn=SENTRY_DSN,
            environment=os.getenv("ENV", "local"),
            traces_sample_rate=float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.1")),
            send_default_pii=False,
        )
        logger.info("Worker Sentry enabled")
    except Exception as e:
        logger.warning(f"Worker Sentry init failed: {e}")


REDIS_URL = os.getenv("REDIS_URL", "").strip()
if not REDIS_URL:
    raise RuntimeError("REDIS_URL must be set to run the ARQ worker")


# ─── ARQ task definitions ──────────────────────────────────
async def generate_quiz_pool(ctx, domain: str):
    """Pre-generate ~100 quiz questions for `domain` and store in Redis."""
    from groq import Groq
    from config import GROQ_API_KEY, GROQ_MODEL_PRIMARY
    from cache import get_redis

    if domain not in {"physics", "ai", "space", "biology", "history",
                      "technology", "nature", "mathematics", "chemistry",
                      "philosophy", "engineering", "ancient_civilizations"}:
        logger.warning(f"unknown domain skipped: {domain}")
        return 0

    prompt = f"""Generate exactly 25 unique multiple-choice quiz questions about {domain}.
Mix difficulties (easy/medium/hard). Each question has exactly 4 options.
Vary correct-answer position. Include a 1-sentence explanation.
Return ONLY JSON:
{{"questions":[{{"q":"...","options":["a","b","c","d"],"correct":0,"explanation":"...","difficulty":"easy|medium|hard"}}]}}"""

    def _call():
        g = Groq(api_key=GROQ_API_KEY)
        resp = g.chat.completions.create(
            model=GROQ_MODEL_PRIMARY,
            messages=[
                {"role": "system", "content": "You are a strict JSON-only quiz generator."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=4500,
            temperature=0.95,
        )
        return resp.choices[0].message.content.strip()

    accumulated = []
    for batch in range(4):  # 4 × 25 = 100 questions
        try:
            raw = await asyncio.to_thread(_call)
        except Exception as e:
            logger.warning(f"groq call failed for {domain} batch {batch}: {e}")
            continue
        cleaned = raw
        if "```" in cleaned:
            cleaned = cleaned.split("```")[1]
            if cleaned.startswith("json"):
                cleaned = cleaned[4:]
            cleaned = cleaned.strip()
        try:
            data = json.loads(cleaned)
            qs = data.get("questions", []) or []
        except Exception as e:
            logger.warning(f"parse failed for {domain} batch {batch}: {e}")
            continue
        for q in qs:
            if (isinstance(q.get("q"), str)
                    and isinstance(q.get("options"), list) and len(q["options"]) == 4
                    and isinstance(q.get("correct"), int) and 0 <= q["correct"] <= 3):
                accumulated.append({
                    "q": q["q"],
                    "options": q["options"],
                    "correct": q["correct"],
                    "explanation": q.get("explanation", ""),
                    "difficulty": q.get("difficulty", "medium"),
                })

    if not accumulated:
        logger.warning(f"quiz pool: empty after generation for {domain}")
        return 0

    r = await get_redis()
    if r is None:
        logger.warning("no redis — pool not stored")
        return 0
    pipe = r.pipeline()
    pipe.delete(f"quiz:pool:{domain}")
    for q in accumulated:
        pipe.rpush(f"quiz:pool:{domain}", json.dumps(q, default=str))
    pipe.expire(f"quiz:pool:{domain}", 12 * 60 * 60)  # 12h backstop
    await pipe.execute()
    logger.info(f"quiz pool: stored {len(accumulated)} questions for {domain}")
    return len(accumulated)


async def refresh_trending_aggregate(ctx):
    """Compute the 24h trending aggregate and stash JSON in Redis."""
    from collections import defaultdict
    from appwrite.query import Query
    from appwrite_client import get_databases
    from config import APPWRITE_DATABASE_ID, COLLECTION_INTERACTIONS, COLLECTION_CONTENT, DOMAINS
    from cache import cache_set_json

    KNOWN = set(DOMAINS)
    db = get_databases()
    cutoff = (datetime.utcnow() - timedelta(hours=24)).strftime("%Y-%m-%dT%H:%M:%S.000+00:00")
    try:
        ir = db.list_documents(
            database_id=APPWRITE_DATABASE_ID,
            collection_id=COLLECTION_INTERACTIONS,
            queries=[Query.greater_than("$createdAt", cutoff), Query.limit(2000)],
        )
        interactions = ir.get("documents", []) or []
    except Exception as e:
        logger.warning(f"trending fetch failed: {e}")
        return 0

    real_cids = list({
        i.get("content_id") for i in interactions
        if i.get("content_id") and i["content_id"] not in KNOWN
    })
    content_domain = {}
    for start in range(0, len(real_cids), 100):
        chunk = real_cids[start:start + 100]
        try:
            cr = db.list_documents(
                database_id=APPWRITE_DATABASE_ID,
                collection_id=COLLECTION_CONTENT,
                queries=[Query.equal("$id", chunk), Query.limit(100)],
            )
            for doc in cr.get("documents", []):
                content_domain[doc["$id"]] = doc.get("domain")
        except Exception:
            continue

    domain_count = defaultdict(int)
    for ia in interactions:
        cid = ia.get("content_id")
        d = cid if cid in KNOWN else content_domain.get(cid)
        if d:
            domain_count[d] += 1

    out = {
        "trending_domains": [
            {"domain": d, "count": c}
            for d, c in sorted(domain_count.items(), key=lambda kv: kv[1], reverse=True)[:10]
        ],
        "total_interactions_24h": sum(domain_count.values()),
        "computed_at": time.time(),
    }
    await cache_set_json("trending:24h", out, ttl=120)
    logger.info(f"trending refreshed: {len(out['trending_domains'])} domains, {out['total_interactions_24h']} hits")
    return len(out["trending_domains"])


async def run_daily_pipeline(ctx):
    """Daily AI pipeline (was APScheduler in main.py:42)."""
    try:
        from agents.orchestrator import run_full_pipeline
        await run_full_pipeline()
        logger.info("daily pipeline complete")
        return "ok"
    except Exception as e:
        logger.error(f"daily pipeline failed: {e}")
        raise


# ─── ARQ worker config ────────────────────────────────────
from arq.connections import RedisSettings
from arq.cron import cron

DOMAINS_LIST = [
    "physics", "ai", "space", "biology", "history",
    "technology", "nature", "mathematics", "chemistry",
    "philosophy", "engineering", "ancient_civilizations",
]


async def quiz_pool_all(ctx):
    """Schedule quiz_pool generation for every domain (called every 6h)."""
    for d in DOMAINS_LIST:
        try:
            await generate_quiz_pool(ctx, d)
        except Exception as e:
            logger.warning(f"quiz pool for {d} failed: {e}")


class WorkerSettings:
    redis_settings = RedisSettings.from_dsn(REDIS_URL)
    functions = [generate_quiz_pool, quiz_pool_all, refresh_trending_aggregate, run_daily_pipeline]
    cron_jobs = [
        cron(refresh_trending_aggregate, minute=set(range(0, 60))),  # every minute
        cron(quiz_pool_all, hour={0, 6, 12, 18}, minute=5),           # every 6h
        cron(run_daily_pipeline, hour=5, minute=0),                   # daily 05:00 UTC
    ]
    keep_result = 60
    max_jobs = 4
    job_timeout = 600
