"""
Blog Agent — Medium-style long-form articles (800-1200 words).
Pipeline: Idea gen → Outline → Research → Draft → Edit pass → Publish

Cost: ~$0.004 per article.
"""
import uuid
import json
import logging
from datetime import datetime

import httpx
from groq import Groq
from tenacity import retry, stop_after_attempt, wait_exponential

from config import GROQ_API_KEY, GROQ_MODEL_PRIMARY, GOOGLE_AI_API_KEY
from s3_client import upload_blog_cover

logger = logging.getLogger(__name__)


def _get_groq():
    return Groq(api_key=GROQ_API_KEY)


# ── Step 1: Idea Generation ───────────────────────────────
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def generate_ideas(domain: str, count: int = 5) -> list[str]:
    """Groq proposes topic ideas for the domain."""
    groq = _get_groq()
    resp = groq.chat.completions.create(
        model=GROQ_MODEL_PRIMARY,
        messages=[
            {
                "role": "system",
                "content": (
                    f"You are a senior science editor. Propose {count} compelling article topics "
                    f"in the {domain} domain that would interest curious adults. "
                    "Return as a JSON array of strings, nothing else."
                ),
            },
            {"role": "user", "content": f"Give me {count} article ideas for {domain} today ({datetime.utcnow().strftime('%Y-%m-%d')})."},
        ],
        max_tokens=300,
        temperature=0.8,
    )
    text = resp.choices[0].message.content.strip()
    # Parse JSON array
    try:
        if text.startswith("```"):
            text = text.split("```")[1].strip()
            if text.startswith("json"):
                text = text[4:].strip()
        return json.loads(text)
    except json.JSONDecodeError:
        return [line.strip("- •\"'") for line in text.split("\n") if line.strip()][:count]


# ── Step 2: Research ──────────────────────────────────────
async def fetch_research(topic: str) -> str:
    """Fetch facts from Wikipedia API for the topic."""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                "https://en.wikipedia.org/api/rest_v1/page/summary/" + topic.replace(" ", "_"),
            )
            if resp.status_code == 200:
                data = resp.json()
                return data.get("extract", "")
    except Exception as e:
        logger.warning(f"Wikipedia research failed: {e}")
    return ""


# ── Step 3: Draft Article ─────────────────────────────────
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def write_draft(topic: str, research: str, domain: str) -> dict:
    """Groq writes 800-1200 word article in Medium style."""
    groq = _get_groq()
    resp = groq.chat.completions.create(
        model=GROQ_MODEL_PRIMARY,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a senior science editor at Medium. Write in a clear, curious, authoritative voice. "
                    "Format: ## Introduction (120w) · ## Section 1 (280w) · ## Section 2 (280w) · ## Section 3 (280w) · ## Conclusion (80w). "
                    "Rules: Every factual claim must have a citation. No first-person. No opinion. "
                    "Write in markdown. Include 2-3 citation links at the bottom."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Topic: {topic}\nDomain: {domain}\n"
                    f"Research context: {research[:2000]}\n"
                    f"Date: {datetime.utcnow().strftime('%Y-%m-%d')}\n"
                    "Write the article now."
                ),
            },
        ],
        max_tokens=2000,
        temperature=0.6,
    )

    body_md = resp.choices[0].message.content.strip()

    # Extract citations from the markdown
    citations = []
    for line in body_md.split("\n"):
        if line.strip().startswith("[") and "http" in line:
            citations.append(line.strip())

    # Calculate read time (~200 words per minute)
    word_count = len(body_md.split())
    read_time_min = max(1, round(word_count / 200))

    return {
        "body_md": body_md,
        "citations": citations,
        "word_count": word_count,
        "read_time_min": read_time_min,
    }


# ── Step 4: Edit Pass ─────────────────────────────────────
@retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=2, max=10))
def edit_pass(body_md: str, domain: str) -> dict:
    """Second Groq call — removes opinion, enforces neutral tone, scores quality."""
    groq = _get_groq()
    resp = groq.chat.completions.create(
        model=GROQ_MODEL_PRIMARY,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an editorial quality reviewer. Review the article below and: "
                    "1. Remove any first-person or opinion language. "
                    "2. Ensure neutral, factual tone throughout. "
                    "3. Score the article 0-100 for quality (factual accuracy, readability, structure). "
                    "Return JSON: {\"edited_body\": \"...\", \"quality_score\": N, \"excerpt\": \"2-sentence summary\"}"
                ),
            },
            {"role": "user", "content": body_md},
        ],
        max_tokens=2500,
        temperature=0.3,
    )

    text = resp.choices[0].message.content.strip()
    try:
        if "```" in text:
            text = text.split("```")[1].strip()
            if text.startswith("json"):
                text = text[4:].strip()
        return json.loads(text)
    except json.JSONDecodeError:
        # Fallback: use original body
        return {
            "edited_body": body_md,
            "quality_score": 75,
            "excerpt": body_md[:200],
        }


# ── Step 5: Generate Cover Image ──────────────────────────
async def generate_cover_image(topic: str, domain: str, blog_id: str) -> str:
    """Gemini Veo 2 — generate blog cover image and upload to S3."""
    if not GOOGLE_AI_API_KEY:
        return ""

    try:
        import google.generativeai as genai
        genai.configure(api_key=GOOGLE_AI_API_KEY)

        model = genai.ImageGenerationModel("imagen-3.0-generate-002")
        result = model.generate_images(
            prompt=f"Modern editorial illustration for an article about {topic}. Clean, professional, no text. Landscape 16:9.",
            number_of_images=1,
            aspect_ratio="16:9",
        )
        if result.images:
            return upload_blog_cover(result.images[0]._image_bytes, domain, blog_id)
    except Exception as e:
        logger.error(f"Blog cover generation failed: {e}")
    return ""


# ── Full Pipeline ──────────────────────────────────────────
async def run_blog_agent(domain: str) -> dict:
    """
    Run the full Blog Agent pipeline for a domain.
    Returns dict with article metadata.
    """
    blog_id = f"blog_{uuid.uuid4().hex[:12]}"
    logger.info(f"[BlogAgent] Starting for domain={domain}, id={blog_id}")

    # Step 1: Generate ideas
    ideas = generate_ideas(domain)
    topic = ideas[0] if ideas else f"Latest developments in {domain}"
    logger.info(f"[BlogAgent] Topic: {topic}")

    # Step 2: Research
    research = await fetch_research(topic)
    logger.info(f"[BlogAgent] Research fetched ({len(research)} chars)")

    # Step 3: Draft
    draft = write_draft(topic, research, domain)
    logger.info(f"[BlogAgent] Draft written ({draft['word_count']} words)")

    # Step 4: Edit pass
    edited = edit_pass(draft["body_md"], domain)
    quality_score = edited.get("quality_score", 75)
    final_body = edited.get("edited_body", draft["body_md"])
    excerpt = edited.get("excerpt", final_body[:200])
    logger.info(f"[BlogAgent] Edit pass complete, quality={quality_score}")

    # Step 5: Cover image
    s3_cover_url = await generate_cover_image(topic, domain, blog_id)

    return {
        "blog_id": blog_id,
        "domain": domain,
        "title": topic,
        "body": final_body,
        "excerpt": excerpt,
        "s3_cover_url": s3_cover_url,
        "citations": draft.get("citations", []),
        "read_time_min": draft.get("read_time_min", 3),
        "quality_score": quality_score,
        "author_type": "ai_agent",
        "content_type": "article",
    }
