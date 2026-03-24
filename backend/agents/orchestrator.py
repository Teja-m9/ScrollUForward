"""
Orchestrator / Supervisor — LangChain-style parallel agent execution.

Every morning at 5:00 AM UTC:
1. CRON fires
2. Supervisor fans out 3 agents in parallel
3. Validation gate checks all output
4. Domain router writes to Appwrite + S3
5. By 6:00 AM all 12 domain pages are refreshed.
"""
import asyncio
import logging
from datetime import datetime

from agents.reel_agent import run_reel_agent
from agents.blog_agent import run_blog_agent
from agents.news_agent import run_news_agent
from agents.validation import validate_batch
from agents.domain_router import route_and_publish
from config import DOMAINS

logger = logging.getLogger(__name__)

# Rotate domains — 5 per day from the 12 total
def get_todays_domains(count: int = 5) -> list[str]:
    """Rotate through domains based on day of year."""
    day = datetime.utcnow().timetuple().tm_yday
    start = (day * count) % len(DOMAINS)
    selected = []
    for i in range(count):
        selected.append(DOMAINS[(start + i) % len(DOMAINS)])
    return selected


async def run_reel_batch(domains: list[str]) -> list[dict]:
    """Run Reel Agent in parallel across domains."""
    tasks = [run_reel_agent(domain) for domain in domains]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    reels = []
    for r in results:
        if isinstance(r, Exception):
            logger.error(f"[Orchestrator] Reel agent failed: {r}")
        elif isinstance(r, dict):
            reels.append(r)
    return reels


async def run_blog_batch(domains: list[str]) -> list[dict]:
    """Run Blog Agent in parallel across domains."""
    tasks = [run_blog_agent(domain) for domain in domains]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    blogs = []
    for r in results:
        if isinstance(r, Exception):
            logger.error(f"[Orchestrator] Blog agent failed: {r}")
        elif isinstance(r, dict):
            blogs.append(r)
    return blogs


async def run_full_pipeline(domains: list[str] | None = None) -> dict:
    """
    Run the complete morning pipeline:
    1. Fan out 3 agents in parallel
    2. Validate all output
    3. Route to Appwrite + S3

    Returns pipeline execution summary.
    """
    start_time = datetime.utcnow()
    if domains is None:
        domains = get_todays_domains()

    logger.info(f"[Orchestrator] === PIPELINE START === domains={domains}")

    # ── Step 1: Run all 3 agents in parallel ──────────────
    reel_task = run_reel_batch(domains)
    blog_task = run_blog_batch(domains)
    news_task = run_news_agent()

    reels, blogs, news_items = await asyncio.gather(
        reel_task, blog_task, news_task,
        return_exceptions=False,
    )

    logger.info(
        f"[Orchestrator] Agents complete: "
        f"{len(reels)} reels, {len(blogs)} blogs, {len(news_items)} news"
    )

    # ── Step 2: Validation gate ───────────────────────────
    all_items = reels + blogs + news_items
    validated = validate_batch(all_items)

    logger.info(f"[Orchestrator] Validation: {len(validated)}/{len(all_items)} passed")

    # ── Step 3: Domain router → Appwrite + S3 ─────────────
    publish_results = route_and_publish(validated)

    end_time = datetime.utcnow()
    duration = (end_time - start_time).total_seconds()

    summary = {
        "status": "completed",
        "started_at": start_time.isoformat(),
        "completed_at": end_time.isoformat(),
        "duration_seconds": round(duration, 1),
        "domains": domains,
        "agents": {
            "reels_generated": len(reels),
            "blogs_generated": len(blogs),
            "news_harvested": len(news_items),
        },
        "validation": {
            "total_input": len(all_items),
            "passed": len(validated),
            "rejected": len(all_items) - len(validated),
        },
        "published": {
            "reels": len(publish_results.get("reels", [])),
            "blogs": len(publish_results.get("blogs", [])),
            "news": len(publish_results.get("news", [])),
            "failed": len(publish_results.get("failed", [])),
        },
    }

    logger.info(f"[Orchestrator] === PIPELINE COMPLETE === duration={duration:.1f}s")
    logger.info(f"[Orchestrator] Summary: {summary}")

    return summary


async def run_single_agent(agent_type: str, domain: str = "technology") -> dict:
    """Run a single agent for testing/manual triggers."""
    if agent_type == "reel":
        result = await run_reel_agent(domain)
        # Reels are always educational — skip validation, publish directly
        publish_results = route_and_publish([result])
        return {"status": "published", "result": publish_results}

    elif agent_type == "blog":
        result = await run_blog_agent(domain)
        validated = validate_batch([result])
        if validated:
            publish_results = route_and_publish(validated)
            return {"status": "published", "result": publish_results}
        return {"status": "rejected_by_validation", "result": result}

    elif agent_type == "news":
        results = await run_news_agent()
        validated = validate_batch(results)
        if validated:
            publish_results = route_and_publish(validated)
            return {"status": "published", "count": len(validated), "result": publish_results}
        return {"status": "no_articles_passed", "count": 0}

    return {"status": "error", "message": f"Unknown agent type: {agent_type}"}
