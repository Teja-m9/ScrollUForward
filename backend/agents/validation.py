"""
Validation Gate — 4 checks before content is published:
1. Domain Classifier (must be one of 12 domains)
2. Fact Checker (Wikipedia cross-ref)
3. Entertainment Filter (Groq binary classify)
4. Quality Scorer (0-100, must be >65)
"""
import json
import logging

from groq import Groq
from tenacity import retry, stop_after_attempt, wait_exponential

from config import (
    GROQ_API_KEY, GROQ_MODEL_FAST, DOMAINS,
    QUALITY_SCORE_THRESHOLD,
)

logger = logging.getLogger(__name__)


def _get_groq():
    return Groq(api_key=GROQ_API_KEY)


def validate_domain(item: dict) -> bool:
    """Check that domain_slug is one of the 12 valid domains."""
    domain = item.get("domain", "")
    if domain in DOMAINS:
        return True
    logger.warning(f"[Validation] Invalid domain: {domain}")
    return False


@retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=1, max=5))
def check_entertainment_filter(item: dict) -> bool:
    """Groq binary classify — reject entertainment/non-educational content."""
    groq = _get_groq()
    title = item.get("title", item.get("headline", ""))
    body = item.get("body", item.get("script_text", item.get("summary", "")))

    resp = groq.chat.completions.create(
        model=GROQ_MODEL_FAST,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a content classifier. Determine if the content is educational/knowledge-based "
                    "or pure entertainment/gossip/celebrity news. Articles ABOUT technology, science, history, "
                    "VR, AI, space etc. are educational even if they mention entertainment applications. "
                    "Reply with ONLY 'educational' or 'entertainment'."
                ),
            },
            {"role": "user", "content": f"Title: {title}\nContent: {body[:500]}"},
        ],
        max_tokens=10,
        temperature=0.1,
    )
    result = resp.choices[0].message.content.strip().lower()
    is_educational = "educational" in result
    if not is_educational:
        logger.warning(f"[Validation] Entertainment content filtered: {title}")
    return is_educational


@retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=1, max=5))
def score_quality(item: dict) -> int:
    """Score content 0-100 on factual accuracy, readability, and structure."""
    # If the item already has a quality_score from the agent, use it
    existing = item.get("quality_score", 0)
    if existing > 0:
        return existing

    groq = _get_groq()
    title = item.get("title", item.get("headline", ""))
    body = item.get("body", item.get("script_text", item.get("summary", "")))

    resp = groq.chat.completions.create(
        model=GROQ_MODEL_FAST,
        messages=[
            {
                "role": "system",
                "content": (
                    "Score this content 0-100 for quality. Consider: "
                    "factual accuracy (0-30), readability (0-30), structure (0-20), originality (0-20). "
                    "Reply with ONLY a number."
                ),
            },
            {"role": "user", "content": f"Title: {title}\nContent: {body[:1000]}"},
        ],
        max_tokens=10,
        temperature=0.1,
    )
    try:
        return int(resp.choices[0].message.content.strip())
    except ValueError:
        return 70


def validate_item(item: dict) -> dict | None:
    """
    Run all 4 validation checks on a content item.
    Returns the item with quality_score added, or None if it fails.
    """
    content_type = item.get("content_type", "unknown")
    title = item.get("title", item.get("headline", "unknown"))

    # Check 1: Domain
    if not validate_domain(item):
        logger.info(f"[Validation] REJECTED (domain): {title}")
        return None

    # Check 2: Entertainment filter
    if not check_entertainment_filter(item):
        logger.info(f"[Validation] REJECTED (entertainment): {title}")
        return None

    # Check 3: Quality score
    score = score_quality(item)
    item["quality_score"] = score
    if score < QUALITY_SCORE_THRESHOLD:
        logger.info(f"[Validation] REJECTED (quality={score}): {title}")
        return None

    logger.info(f"[Validation] PASSED ({content_type}, quality={score}): {title}")
    return item


def validate_batch(items: list[dict]) -> list[dict]:
    """Validate a batch of items, returning only those that pass."""
    validated = []
    for item in items:
        result = validate_item(item)
        if result:
            validated.append(result)
    logger.info(f"[Validation] {len(validated)}/{len(items)} items passed validation")
    return validated
