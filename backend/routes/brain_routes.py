"""
Brain Fingerprint — compute a per-user knowledge graph from interactions + posts.

Nodes are knowledge domains sized by how much the user has engaged with them.
Edges are semantically-related domain pairs whose strength only counts if
BOTH endpoints are active for that user. No two users' graphs look identical.
"""
import logging
from collections import defaultdict
from fastapi import APIRouter, Depends, HTTPException, Query as QueryParam
from appwrite.query import Query

from auth import get_current_user
from appwrite_client import get_databases
from config import (
    APPWRITE_DATABASE_ID,
    COLLECTION_INTERACTIONS,
    COLLECTION_CONTENT,
    DOMAINS,
)
from cache import cached

KNOWN_DOMAINS = set(DOMAINS)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/brain", tags=["Brain Map"])


# Semantic relatedness graph across knowledge domains.
# (from, to, strength 0..1)
RELATED_DOMAINS = [
    ("physics", "space", 0.95),
    ("physics", "mathematics", 0.85),
    ("physics", "chemistry", 0.78),
    ("physics", "engineering", 0.75),
    ("physics", "ai", 0.45),

    ("ai", "technology", 0.95),
    ("ai", "mathematics", 0.75),
    ("ai", "philosophy", 0.6),
    ("ai", "biology", 0.4),

    ("biology", "nature", 0.9),
    ("biology", "chemistry", 0.85),
    ("biology", "ancient_civilizations", 0.3),

    ("chemistry", "mathematics", 0.55),
    ("chemistry", "engineering", 0.6),

    ("space", "ai", 0.6),
    ("space", "technology", 0.55),
    ("space", "mathematics", 0.7),
    ("space", "history", 0.45),

    ("history", "philosophy", 0.8),
    ("history", "ancient_civilizations", 0.95),
    ("history", "nature", 0.35),

    ("philosophy", "mathematics", 0.5),
    ("philosophy", "ancient_civilizations", 0.6),

    ("engineering", "technology", 0.9),
    ("engineering", "mathematics", 0.7),

    ("mathematics", "technology", 0.7),

    ("nature", "ancient_civilizations", 0.3),
    ("nature", "space", 0.4),
]

# Weight applied to each interaction type when accumulating domain scores.
INTERACTION_WEIGHTS = {
    "watch_reel":      1,
    "read_article":    3,
    "complete_quiz":   5,
    "post_discussion": 7,
    "streak_bonus":    2,
    "viral_content":  10,
    "like":            1,
    "save":            2,
    "share":           2,
    "comment":         3,
}

# Authoring your own content is the strongest possible signal
AUTHOR_WEIGHT = 8


@router.get("/fingerprint")
@cached(ttl=300, key_fn=lambda current_user: f"brain:fingerprint:{current_user['sub']}")
async def brain_map(current_user: dict = Depends(get_current_user)):
    """Return the current user's knowledge fingerprint as a node/edge graph."""
    db = get_databases()
    uid = current_user["sub"]

    # ── Pull this user's interactions (cap 500 for the map) ──────
    try:
        ir = db.list_documents(
            database_id=APPWRITE_DATABASE_ID,
            collection_id=COLLECTION_INTERACTIONS,
            queries=[Query.equal("user_id", uid), Query.limit(500)],
        )
        interactions = ir.get("documents", []) or []
    except Exception as e:
        logger.warning(f"brain-map: interactions fetch failed: {e}")
        interactions = []

    # ── Batch-fetch the content touched by those interactions ──
    content_ids = list({
        i.get("content_id") for i in interactions if i.get("content_id")
    })
    content_by_id = {}
    for start in range(0, len(content_ids), 100):
        chunk = content_ids[start:start + 100]
        try:
            cr = db.list_documents(
                database_id=APPWRITE_DATABASE_ID,
                collection_id=COLLECTION_CONTENT,
                queries=[Query.equal("$id", chunk), Query.limit(100)],
            )
            for doc in cr.get("documents", []):
                content_by_id[doc["$id"]] = doc
        except Exception as e:
            logger.warning(f"brain-map: content chunk fetch failed: {e}")

    # ── Accumulate weighted domain scores ────────────────────────
    domain_weight = defaultdict(float)
    domain_interactions = defaultdict(int)

    for ia in interactions:
        cid = ia.get("content_id")
        itype = ia.get("interaction_type", "watch_reel")

        # Resolve the domain. Two paths:
        #   1) cid points at a real content doc we fetched → read doc.domain
        #   2) cid is itself a known domain string (quiz flow sends this)
        domain = None
        if cid:
            content = content_by_id.get(cid)
            if content:
                domain = content.get("domain")
            elif cid in KNOWN_DOMAINS:
                domain = cid

        if not domain:
            continue
        w = INTERACTION_WEIGHTS.get(itype, 1)
        domain_weight[domain] += w
        domain_interactions[domain] += 1

    # ── User's own posts → strongest signal ──────────────────────
    try:
        pr = db.list_documents(
            database_id=APPWRITE_DATABASE_ID,
            collection_id=COLLECTION_CONTENT,
            queries=[Query.equal("author_id", uid), Query.limit(200)],
        )
        posts = pr.get("documents", []) or []
    except Exception as e:
        logger.warning(f"brain-map: posts fetch failed: {e}")
        posts = []

    domain_posts = defaultdict(int)
    for p in posts:
        d = p.get("domain")
        if d:
            domain_weight[d] += AUTHOR_WEIGHT
            domain_posts[d] += 1

    # ── Build node / edge payload ────────────────────────────────
    nodes = [
        {
            "domain": d,
            "weight": round(w, 2),
            "interactions": domain_interactions.get(d, 0),
            "posts": domain_posts.get(d, 0),
        }
        for d, w in sorted(domain_weight.items(), key=lambda kv: kv[1], reverse=True)
    ]

    active = set(domain_weight.keys())
    edges = [
        {"from": a, "to": b, "strength": s}
        for a, b, s in RELATED_DOMAINS
        if a in active and b in active
    ]

    return {
        "nodes": nodes,
        "edges": edges,
        "total_interactions": len(interactions),
        "total_posts": len(posts),
        "unique_domains": len(active),
    }


@router.get("/history")
async def brain_history(
    domain: str = QueryParam(..., description="Domain to show history for"),
    limit: int = QueryParam(30, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
):
    """Return this user's recent interactions that belong to a given domain."""
    if domain not in KNOWN_DOMAINS:
        raise HTTPException(status_code=400, detail=f"Unknown domain: {domain}")

    db = get_databases()
    uid = current_user["sub"]

    try:
        ir = db.list_documents(
            database_id=APPWRITE_DATABASE_ID,
            collection_id=COLLECTION_INTERACTIONS,
            queries=[
                Query.equal("user_id", uid),
                Query.order_desc("$createdAt"),
                Query.limit(500),
            ],
        )
        interactions = ir.get("documents", []) or []
    except Exception as e:
        logger.warning(f"history: interactions fetch failed: {e}")
        interactions = []

    # Batch-fetch content for real content_ids
    real_ids = list({i.get("content_id") for i in interactions
                     if i.get("content_id") and i.get("content_id") not in KNOWN_DOMAINS})
    content_by_id = {}
    for start in range(0, len(real_ids), 100):
        chunk = real_ids[start:start + 100]
        try:
            cr = db.list_documents(
                database_id=APPWRITE_DATABASE_ID,
                collection_id=COLLECTION_CONTENT,
                queries=[Query.equal("$id", chunk), Query.limit(100)],
            )
            for doc in cr.get("documents", []):
                content_by_id[doc["$id"]] = doc
        except Exception as e:
            logger.warning(f"history: content fetch failed: {e}")

    items = []
    for ia in interactions:
        cid = ia.get("content_id")
        itype = ia.get("interaction_type", "")
        created = ia.get("$createdAt", "")

        # Resolve domain
        matched_domain = None
        title = None
        content_type = None
        if cid in KNOWN_DOMAINS:
            matched_domain = cid
            title = f"{itype.replace('_', ' ').title()} — {cid}"
            content_type = "action"
        else:
            content = content_by_id.get(cid)
            if content:
                matched_domain = content.get("domain")
                title = content.get("title") or content.get("body", "")[:60]
                content_type = content.get("content_type", "content")

        if matched_domain != domain:
            continue

        items.append({
            "id": ia.get("$id"),
            "interaction_type": itype,
            "content_id": cid,
            "title": (title or "Untitled")[:120],
            "content_type": content_type or "content",
            "at": created,
        })
        if len(items) >= limit:
            break

    return {"domain": domain, "count": len(items), "items": items}
