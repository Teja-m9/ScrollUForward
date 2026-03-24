"""
News Agent — harvest, score, summarise, bias-check across 200+ sources.
Pipeline: RSS harvest → Groq relevance score → Top-10 select → Summarise → Bias check → Publish

Pulls articles from verified science/knowledge sources, scores for relevance,
selects top 10 across all 12 domains (max 2 per domain), writes neutral summaries.
"""
import uuid
import json
import logging
from datetime import datetime
from collections import defaultdict

import httpx
import feedparser
from groq import Groq
from tenacity import retry, stop_after_attempt, wait_exponential

from config import (
    GROQ_API_KEY, GROQ_MODEL_PRIMARY, GROQ_MODEL_FAST,
    NEWSAPI_KEY, NEWS_RSS_FEEDS, DOMAINS,
    QUALITY_SCORE_THRESHOLD,
)

logger = logging.getLogger(__name__)


def _get_groq():
    return Groq(api_key=GROQ_API_KEY)


# ── Step 1: Harvest ────────────────────────────────────────
async def harvest_articles() -> list[dict]:
    """Pull articles from RSS feeds + NewsAPI. Deduplicate by URL."""
    articles = []
    seen_urls = set()

    # RSS feeds
    for source_name, feed_url in NEWS_RSS_FEEDS.items():
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(feed_url)
                feed = feedparser.parse(resp.text)
                for entry in feed.entries[:20]:
                    url = entry.get("link", "")
                    if url and url not in seen_urls:
                        seen_urls.add(url)
                        articles.append({
                            "headline": entry.get("title", ""),
                            "description": entry.get("summary", entry.get("description", "")),
                            "source_name": source_name,
                            "source_url": url,
                            "published": entry.get("published", ""),
                        })
        except Exception as e:
            logger.warning(f"RSS fetch failed for {source_name}: {e}")

    # NewsAPI (if key provided)
    if NEWSAPI_KEY:
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(
                    "https://newsapi.org/v2/top-headlines",
                    params={"category": "science", "language": "en", "pageSize": 50, "apiKey": NEWSAPI_KEY},
                )
                data = resp.json()
                for art in data.get("articles", []):
                    url = art.get("url", "")
                    if url and url not in seen_urls:
                        seen_urls.add(url)
                        articles.append({
                            "headline": art.get("title", ""),
                            "description": art.get("description", ""),
                            "source_name": art.get("source", {}).get("name", "NewsAPI"),
                            "source_url": url,
                            "published": art.get("publishedAt", ""),
                        })
        except Exception as e:
            logger.warning(f"NewsAPI fetch failed: {e}")

    logger.info(f"[NewsAgent] Harvested {len(articles)} articles from {len(NEWS_RSS_FEEDS)} feeds")
    return articles


# ── Step 2: Relevance Scoring ──────────────────────────────
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def score_articles(articles: list[dict]) -> list[dict]:
    """Groq scores each article 0-100 and assigns a domain_slug."""
    if not articles:
        return []

    groq = _get_groq()
    # Process in batches of 10
    scored = []
    for i in range(0, len(articles), 10):
        batch = articles[i:i+10]
        batch_text = "\n".join(
            f"{j+1}. [{a['source_name']}] {a['headline']}: {a['description'][:150]}"
            for j, a in enumerate(batch)
        )

        resp = groq.chat.completions.create(
            model=GROQ_MODEL_FAST,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Score each article for educational/knowledge value. "
                        f"Valid domains: {json.dumps(DOMAINS)}. "
                        "Return JSON array: [{\"index\": 1, \"score\": 85, \"domain\": \"physics\", "
                        "\"domain_match\": 25, \"novelty\": 20, \"credibility\": 22, \"readability\": 18}]. "
                        "Score breakdown: domain_match (0-30), novelty (0-25), credibility (0-25), readability (0-20). "
                        "Total = sum of all four. Only return valid JSON."
                    ),
                },
                {"role": "user", "content": batch_text},
            ],
            max_tokens=800,
            temperature=0.2,
        )

        text = resp.choices[0].message.content.strip()
        try:
            if "```" in text:
                text = text.split("```")[1].strip()
                if text.startswith("json"):
                    text = text[4:].strip()
            scores = json.loads(text)
            for s in scores:
                idx = s.get("index", 1) - 1
                if 0 <= idx < len(batch):
                    batch[idx]["score"] = s.get("score", 0)
                    batch[idx]["domain"] = s.get("domain", "technology")
                    batch[idx]["credibility_score"] = s.get("credibility", 15)
        except json.JSONDecodeError:
            for a in batch:
                a["score"] = 50
                a["domain"] = "technology"
                a["credibility_score"] = 15

        scored.extend(batch)

    return scored


# ── Step 3: Top-10 Selection ──────────────────────────────
def select_top_articles(scored: list[dict], max_total: int = 10, max_per_domain: int = 2) -> list[dict]:
    """Select highest-scoring articles, max 2 per domain, balanced."""
    sorted_articles = sorted(scored, key=lambda x: x.get("score", 0), reverse=True)
    domain_counts = defaultdict(int)
    selected = []

    for article in sorted_articles:
        if len(selected) >= max_total:
            break
        domain = article.get("domain", "technology")
        if domain_counts[domain] < max_per_domain:
            if article.get("score", 0) >= QUALITY_SCORE_THRESHOLD:
                selected.append(article)
                domain_counts[domain] += 1

    # If we don't have enough, lower the threshold
    if len(selected) < max_total:
        for article in sorted_articles:
            if len(selected) >= max_total:
                break
            if article not in selected:
                domain = article.get("domain", "technology")
                if domain_counts[domain] < max_per_domain:
                    selected.append(article)
                    domain_counts[domain] += 1

    return selected


# ── Step 4: Summarise ─────────────────────────────────────
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def summarise_articles(articles: list[dict]) -> list[dict]:
    """Groq generates 3-sentence neutral summary for each article."""
    groq = _get_groq()

    for article in articles:
        resp = groq.chat.completions.create(
            model=GROQ_MODEL_FAST,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Write a 3-sentence neutral summary. No opinion. No clickbait. "
                        "Factual and concise. Just the summary text, nothing else."
                    ),
                },
                {
                    "role": "user",
                    "content": f"Headline: {article['headline']}\nDescription: {article.get('description', '')}",
                },
            ],
            max_tokens=200,
            temperature=0.3,
        )
        article["summary"] = resp.choices[0].message.content.strip()

    return articles


# ── Step 5: Bias Check ────────────────────────────────────
@retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=2, max=10))
def bias_check(articles: list[dict]) -> list[dict]:
    """Sentiment NLP pass — flag political language, auto-discard if biased."""
    groq = _get_groq()
    batch_text = "\n".join(
        f"{i+1}. {a['summary']}" for i, a in enumerate(articles)
    )

    resp = groq.chat.completions.create(
        model=GROQ_MODEL_FAST,
        messages=[
            {
                "role": "system",
                "content": (
                    "Check each summary for political bias or inflammatory language. "
                    "Return JSON array: [{\"index\": 1, \"bias_flag\": false}]. "
                    "Set bias_flag=true ONLY if the text contains political propaganda, "
                    "inflammatory rhetoric, or clear ideological bias. Science content is not biased. "
                    "Only return valid JSON."
                ),
            },
            {"role": "user", "content": batch_text},
        ],
        max_tokens=400,
        temperature=0.1,
    )

    text = resp.choices[0].message.content.strip()
    try:
        if "```" in text:
            text = text.split("```")[1].strip()
            if text.startswith("json"):
                text = text[4:].strip()
        flags = json.loads(text)
        for f in flags:
            idx = f.get("index", 1) - 1
            if 0 <= idx < len(articles):
                articles[idx]["bias_flag"] = f.get("bias_flag", False)
    except json.JSONDecodeError:
        for a in articles:
            a["bias_flag"] = False

    # Remove biased articles
    return [a for a in articles if not a.get("bias_flag", False)]


# ── Full Pipeline ──────────────────────────────────────────
async def run_news_agent() -> list[dict]:
    """
    Run the full News Agent pipeline.
    Returns list of dicts with news metadata.
    """
    logger.info("[NewsAgent] Starting harvest...")

    # Step 1: Harvest
    raw_articles = await harvest_articles()
    if not raw_articles:
        logger.warning("[NewsAgent] No articles harvested")
        return []

    # Step 2: Score
    scored = score_articles(raw_articles)
    logger.info(f"[NewsAgent] Scored {len(scored)} articles")

    # Step 3: Select top 10
    top_articles = select_top_articles(scored)
    logger.info(f"[NewsAgent] Selected {len(top_articles)} top articles")

    # Step 4: Summarise
    summarised = summarise_articles(top_articles)

    # Step 5: Bias check
    clean_articles = bias_check(summarised)
    logger.info(f"[NewsAgent] {len(clean_articles)} articles passed bias check")

    # Format output
    results = []
    for article in clean_articles:
        news_id = f"news_{uuid.uuid4().hex[:12]}"
        results.append({
            "news_id": news_id,
            "domain": article.get("domain", "technology"),
            "headline": article.get("headline", ""),
            "summary": article.get("summary", ""),
            "source_name": article.get("source_name", ""),
            "source_url": article.get("source_url", ""),
            "credibility_score": article.get("credibility_score", 50),
            "bias_flag": False,
            "content_type": "news",
        })

    return results
