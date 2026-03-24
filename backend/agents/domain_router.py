"""
Domain Router — reads domain_slug from each validated content item,
routes to the correct Appwrite collection and S3 folder.

Writes metadata to Appwrite, media to S3, assembles CloudFront URLs.
"""
import json
import logging
from datetime import datetime

from appwrite.id import ID
from appwrite_client import get_databases
from config import APPWRITE_DATABASE_ID, COLLECTION_CONTENT

logger = logging.getLogger(__name__)


def publish_reel(item: dict) -> dict:
    """Write a validated reel to Appwrite content collection."""
    db = get_databases()
    doc_id = item.get("reel_id", ID.unique())

    try:
        doc = db.create_document(
            database_id=APPWRITE_DATABASE_ID,
            collection_id=COLLECTION_CONTENT,
            document_id=doc_id,
            data={
                "title": item.get("title", ""),
                "body": item.get("script_text", ""),
                "content_type": "reel",
                "domain": item.get("domain", ""),
                "author_id": "system_agent",
                "author_username": "ScrollUForward AI",
                "author_avatar": "",
                "thumbnail_url": item.get("s3_thumb_url", ""),
                "media_url": item.get("s3_video_url", ""),
                "citations": json.dumps([]),
                "tags": json.dumps([item.get("domain", "")]),
                "quality_score": item.get("quality_score", 80),
                "likes_count": 0,
                "saves_count": 0,
                "views_count": 0,
                "comments_count": 0,
            },
        )
        logger.info(f"[DomainRouter] Published reel: {doc['$id']} → {item.get('domain')}")
        return {"id": doc["$id"], "status": "published", **item}
    except Exception as e:
        logger.error(f"[DomainRouter] Failed to publish reel: {e}")
        return {"id": doc_id, "status": "failed", "error": str(e), **item}


def publish_blog(item: dict) -> dict:
    """Write a validated blog article to Appwrite content collection."""
    db = get_databases()
    doc_id = item.get("blog_id", ID.unique())

    try:
        doc = db.create_document(
            database_id=APPWRITE_DATABASE_ID,
            collection_id=COLLECTION_CONTENT,
            document_id=doc_id,
            data={
                "title": item.get("title", ""),
                "body": item.get("body", ""),
                "content_type": "article",
                "domain": item.get("domain", ""),
                "author_id": "system_agent",
                "author_username": "ScrollUForward AI",
                "author_avatar": "",
                "thumbnail_url": item.get("s3_cover_url", ""),
                "media_url": "",
                "citations": json.dumps(item.get("citations", [])),
                "tags": json.dumps([item.get("domain", "")]),
                "quality_score": item.get("quality_score", 80),
                "likes_count": 0,
                "saves_count": 0,
                "views_count": 0,
                "comments_count": 0,
            },
        )
        logger.info(f"[DomainRouter] Published blog: {doc['$id']} → {item.get('domain')}")
        return {"id": doc["$id"], "status": "published", **item}
    except Exception as e:
        logger.error(f"[DomainRouter] Failed to publish blog: {e}")
        return {"id": doc_id, "status": "failed", "error": str(e), **item}


def publish_news(item: dict) -> dict:
    """Write a validated news item to Appwrite content collection."""
    db = get_databases()
    doc_id = item.get("news_id", ID.unique())

    try:
        doc = db.create_document(
            database_id=APPWRITE_DATABASE_ID,
            collection_id=COLLECTION_CONTENT,
            document_id=doc_id,
            data={
                "title": item.get("headline", ""),
                "body": item.get("summary", ""),
                "content_type": "news",
                "domain": item.get("domain", ""),
                "author_id": "system_agent",
                "author_username": item.get("source_name", "ScrollUForward AI"),
                "author_avatar": "",
                "thumbnail_url": "",
                "media_url": item.get("source_url", ""),
                "citations": json.dumps([item.get("source_url", "")]),
                "tags": json.dumps([item.get("domain", "")]),
                "quality_score": item.get("credibility_score", 70),
                "likes_count": 0,
                "saves_count": 0,
                "views_count": 0,
                "comments_count": 0,
            },
        )
        logger.info(f"[DomainRouter] Published news: {doc['$id']} → {item.get('domain')}")
        return {"id": doc["$id"], "status": "published", **item}
    except Exception as e:
        logger.error(f"[DomainRouter] Failed to publish news: {e}")
        return {"id": doc_id, "status": "failed", "error": str(e), **item}


def route_and_publish(validated_items: list[dict]) -> dict:
    """
    Route each validated item to the correct publisher based on content_type.
    Returns summary of published content.
    """
    results = {"reels": [], "blogs": [], "news": [], "failed": []}

    for item in validated_items:
        content_type = item.get("content_type", "")

        if content_type == "reel":
            result = publish_reel(item)
        elif content_type == "article":
            result = publish_blog(item)
        elif content_type == "news":
            result = publish_news(item)
        else:
            logger.warning(f"[DomainRouter] Unknown content type: {content_type}")
            results["failed"].append(item)
            continue

        if result.get("status") == "published":
            key = {"reel": "reels", "article": "blogs", "news": "news"}[content_type]
            results[key].append(result)
        else:
            results["failed"].append(result)

    logger.info(
        f"[DomainRouter] Published: {len(results['reels'])} reels, "
        f"{len(results['blogs'])} blogs, {len(results['news'])} news. "
        f"Failed: {len(results['failed'])}"
    )
    return results
