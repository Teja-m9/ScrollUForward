"""
Content Service — port 8002
============================
Handles: content feed, CRUD, search, interactions, comments
Redis caching: feed (TTL 5min), individual content items (TTL 30min)
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

import json, logging
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, Query as QP
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from appwrite.id import ID
from appwrite.query import Query

from shared.config import APPWRITE_DATABASE_ID, COLLECTION_CONTENT, COLLECTION_INTERACTIONS, COLLECTION_CONTENT_COMMENTS
from shared.appwrite_client import get_databases
from shared.auth import get_current_user
from shared.redis_client import (
    cache_get, cache_set, cache_delete, cache_delete_pattern,
    key_feed, key_content, get_redis
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [CONTENT] %(message)s")
log = logging.getLogger("content_service")


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        r = get_redis()
        await r.ping()
        log.info("Redis connected")
    except Exception as e:
        log.warning(f"Redis unavailable: {e}")
    yield


app = FastAPI(title="Content Service", version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])


# ── Schemas ───────────────────────────────────────────────────────────────────
class ContentCreate(BaseModel):
    title:        str
    body:         str
    content_type: str   # "reel" | "article" | "news"
    domain:       str
    media_url:    str = ""
    thumbnail_url: str = ""
    tags:         list[str] = []
    quality_score: int = 80

class InteractionCreate(BaseModel):
    interaction_type: str  # "like" | "save" | "view" | "share"


# ── Helpers ───────────────────────────────────────────────────────────────────
def doc_to_content(doc: dict) -> dict:
    tags = doc.get("tags", "[]")
    if isinstance(tags, str):
        try:
            tags = json.loads(tags)
        except Exception:
            tags = []
    return {
        "id":             doc["$id"],
        "title":          doc.get("title", ""),
        "body":           doc.get("body", ""),
        "content_type":   doc.get("content_type", ""),
        "domain":         doc.get("domain", ""),
        "author_id":      doc.get("author_id", ""),
        "author_username": doc.get("author_username", ""),
        "author_avatar":  doc.get("author_avatar", ""),
        "thumbnail_url":  doc.get("thumbnail_url", ""),
        "media_url":      doc.get("media_url", ""),
        "tags":           tags,
        "quality_score":  doc.get("quality_score", 0),
        "likes_count":    doc.get("likes_count", 0),
        "saves_count":    doc.get("saves_count", 0),
        "views_count":    doc.get("views_count", 0),
        "comments_count": doc.get("comments_count", 0),
        "created_at":     doc.get("$createdAt", ""),
    }


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"service": "content", "status": "up"}


@app.get("/content/feed/personalized/")
async def personalized_feed(
    limit:  int = QP(20, ge=1, le=50),
    offset: int = QP(0, ge=0),
    current_user: dict = Depends(get_current_user),
):
    user_id   = current_user["sub"]
    cache_key = key_feed(user_id, offset // limit)

    cached = await cache_get(cache_key)
    if cached:
        log.info(f"[Cache HIT] feed:{user_id}")
        return cached

    db = get_databases()
    try:
        # Get user interest tags
        from shared.appwrite_client import get_databases as gdb
        from shared.config import COLLECTION_USERS
        user_doc = db.get_document(APPWRITE_DATABASE_ID, COLLECTION_USERS, user_id)
        tags_raw = user_doc.get("interest_tags", "[]")
        tags = json.loads(tags_raw) if isinstance(tags_raw, str) else tags_raw
    except Exception:
        tags = []

    # Build queries
    queries = [Query.order_desc("$createdAt"), Query.limit(limit), Query.offset(offset)]

    try:
        # If user has interests, try to fetch domain-matched content first
        if tags:
            domain_query = queries + [Query.equal("domain", tags[0])]
            result = db.list_documents(APPWRITE_DATABASE_ID, COLLECTION_CONTENT, domain_query)
            items = result["documents"]
            # Supplement with general feed if not enough
            if len(items) < limit:
                general = db.list_documents(APPWRITE_DATABASE_ID, COLLECTION_CONTENT, queries)
                seen = {d["$id"] for d in items}
                for doc in general["documents"]:
                    if doc["$id"] not in seen:
                        items.append(doc)
                        if len(items) >= limit:
                            break
        else:
            result = db.list_documents(APPWRITE_DATABASE_ID, COLLECTION_CONTENT, queries)
            items  = result["documents"]

        feed = [doc_to_content(d) for d in items]
        await cache_set(cache_key, feed, ttl=300)  # cache 5 min
        return feed

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/content/")
async def list_content(
    domain:       Optional[str] = QP(None),
    content_type: Optional[str] = QP(None),
    limit:        int = QP(20, ge=1, le=100),
    offset:       int = QP(0),
):
    db = get_databases()
    queries = [Query.order_desc("$createdAt"), Query.limit(limit), Query.offset(offset)]
    if domain:       queries.append(Query.equal("domain", domain))
    if content_type: queries.append(Query.equal("content_type", content_type))

    try:
        result = db.list_documents(APPWRITE_DATABASE_ID, COLLECTION_CONTENT, queries)
        return [doc_to_content(d) for d in result["documents"]]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/content/search/")
async def search_content(q: str = QP(..., min_length=2), limit: int = QP(20)):
    db = get_databases()
    try:
        result = db.list_documents(
            APPWRITE_DATABASE_ID, COLLECTION_CONTENT,
            [Query.search("title", q), Query.limit(limit)],
        )
        return [doc_to_content(d) for d in result["documents"]]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/content/{content_id}")
async def get_content(content_id: str):
    cache_key = key_content(content_id)
    cached    = await cache_get(cache_key)
    if cached:
        return cached

    db = get_databases()
    try:
        doc = db.get_document(APPWRITE_DATABASE_ID, COLLECTION_CONTENT, content_id)
        item = doc_to_content(doc)
        await cache_set(cache_key, item, ttl=1800)  # cache 30 min
        return item
    except Exception:
        raise HTTPException(status_code=404, detail="Content not found")


@app.post("/content/")
async def create_content(req: ContentCreate, current_user: dict = Depends(get_current_user)):
    db      = get_databases()
    doc_id  = ID.unique()
    user_id = current_user["sub"]

    try:
        doc = db.create_document(
            database_id=APPWRITE_DATABASE_ID,
            collection_id=COLLECTION_CONTENT,
            document_id=doc_id,
            data={
                "title":          req.title,
                "body":           req.body,
                "content_type":   req.content_type,
                "domain":         req.domain,
                "author_id":      user_id,
                "author_username": current_user.get("username", ""),
                "author_avatar":  "",
                "thumbnail_url":  req.thumbnail_url,
                "media_url":      req.media_url,
                "citations":      json.dumps([]),
                "tags":           json.dumps(req.tags),
                "quality_score":  req.quality_score,
                "likes_count":    0,
                "saves_count":    0,
                "views_count":    0,
                "comments_count": 0,
            },
        )
        # Invalidate feed cache for this user
        await cache_delete_pattern(f"feed:user:{user_id}:*")
        return doc_to_content(doc)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/content/{content_id}/interact")
async def interact(
    content_id: str,
    req: InteractionCreate,
    current_user: dict = Depends(get_current_user),
):
    """Handle like / save / view / share interactions."""
    db      = get_databases()
    user_id = current_user["sub"]
    itype   = req.interaction_type

    counter_field = {
        "like":  "likes_count",
        "save":  "saves_count",
        "view":  "views_count",
        "share": "views_count",
    }.get(itype)

    if not counter_field:
        raise HTTPException(status_code=400, detail=f"Unknown interaction type: {itype}")

    try:
        doc  = db.get_document(APPWRITE_DATABASE_ID, COLLECTION_CONTENT, content_id)
        curr = doc.get(counter_field, 0)
        db.update_document(
            APPWRITE_DATABASE_ID, COLLECTION_CONTENT, content_id,
            data={counter_field: curr + 1},
        )
        # Save interaction record
        try:
            db.create_document(
                APPWRITE_DATABASE_ID, COLLECTION_INTERACTIONS, ID.unique(),
                data={"user_id": user_id, "content_id": content_id,
                      "interaction_type": itype},
            )
        except Exception:
            pass

        # Invalidate content cache
        await cache_delete(key_content(content_id))
        return {"success": True, "interaction_type": itype, "new_count": curr + 1}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/content/{content_id}/comments")
async def list_comments(content_id: str, limit: int = QP(50)):
    db = get_databases()
    try:
        result = db.list_documents(
            APPWRITE_DATABASE_ID, COLLECTION_CONTENT_COMMENTS,
            [Query.equal("content_id", content_id),
             Query.order_desc("$createdAt"), Query.limit(limit)],
        )
        return [{"id": d["$id"], "user_id": d.get("user_id"), "username": d.get("username"),
                 "body": d.get("body"), "created_at": d.get("$createdAt")}
                for d in result["documents"]]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/content/{content_id}/comments")
async def add_comment(
    content_id: str,
    body: dict,
    current_user: dict = Depends(get_current_user),
):
    db  = get_databases()
    txt = body.get("body", "").strip()
    if not txt:
        raise HTTPException(status_code=400, detail="Comment body required")
    try:
        doc = db.create_document(
            APPWRITE_DATABASE_ID, COLLECTION_CONTENT_COMMENTS, ID.unique(),
            data={"content_id": content_id, "user_id": current_user["sub"],
                  "username": current_user.get("username", ""),
                  "body": txt, "likes_count": 0},
        )
        return {"id": doc["$id"], "body": txt, "created_at": doc.get("$createdAt")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8002, reload=True)
