"""Discussion Service — port 8003
Handles discussion rooms, comments, AI chat, bias detection, moderation.
"""
from __future__ import annotations
import os, sys, time
from datetime import datetime, timezone
from typing import Optional, List

from fastapi import FastAPI, HTTPException, Header, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
from groq import Groq

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))
from microservices.shared.config import (
    APPWRITE_DATABASE_ID, COLLECTION_DISCUSSIONS, COLLECTION_COMMENTS,
    COLLECTION_USERS, GROQ_API_KEY, GROQ_MODEL_PRIMARY, GROQ_MODEL_FAST,
    AUTH_SERVICE_URL, QUALITY_SCORE_THRESHOLD, TEMP_BAN_HOURS,
    MAX_STRIKES_BEFORE_PERMANENT_BAN, COLLECTION_USER_VIOLATIONS,
)
from microservices.shared.appwrite_client import get_db
from microservices.shared.redis_client import (
    cache_get, cache_set, cache_delete_pattern, key_discussions,
)
from microservices.shared.auth import decode_token
from appwrite.id import ID
from appwrite.query import Query as AQ

# ── App ────────────────────────────────────────────────────────────────────
app = FastAPI(title="Discussion Service", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

DISCUSSION_CACHE_TTL = 120   # 2 min
COMMENTS_CACHE_TTL  = 60    # 1 min

# ── Auth helper ────────────────────────────────────────────────────────────
async def current_user(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "Missing bearer token")
    payload = decode_token(authorization[7:])
    if not payload:
        raise HTTPException(401, "Invalid token")
    return payload

async def optional_user(authorization: str = Header(default="")):
    if not authorization.startswith("Bearer "):
        return None
    return decode_token(authorization[7:])

# ── Schemas ────────────────────────────────────────────────────────────────
class CreateDiscussionReq(BaseModel):
    title: str
    description: str = ""
    domain: str = "technology"
    is_ai_room: bool = True

class UpdateDiscussionReq(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None

class CreateCommentReq(BaseModel):
    body: str
    citation_url: str = ""

class AIChatReq(BaseModel):
    message: str
    topic: str
    domain: str = "technology"
    history: List[dict] = []
    discussion_id: str = ""
    user_id: str = ""

class BiasCheckReq(BaseModel):
    text: str
    context: str = ""

# ── Discussion CRUD ────────────────────────────────────────────────────────
@app.post("/discussions/")
async def create_discussion(req: CreateDiscussionReq, user=Depends(current_user)):
    db = get_db()
    now = datetime.now(timezone.utc).isoformat()
    doc = db.create_document(
        APPWRITE_DATABASE_ID, COLLECTION_DISCUSSIONS,
        ID.unique(),
        {
            "title": req.title,
            "description": req.description,
            "domain": req.domain,
            "is_ai_room": req.is_ai_room,
            "created_by": user["user_id"],
            "creator_username": user.get("username", ""),
            "comments_count": 0,
            "participants_count": 1,
            "created_at": now,
            "updated_at": now,
        }
    )
    await cache_delete_pattern(f"discussions:{req.domain}:*")
    return doc

@app.get("/discussions/")
async def list_discussions(
    domain: Optional[str] = None,
    is_ai_room: Optional[bool] = None,
    limit: int = Query(20, le=50),
    offset: int = 0,
):
    cache_key = f"discussions:{domain or 'all'}:{is_ai_room}:{limit}:{offset}"
    cached = await cache_get(cache_key)
    if cached:
        return cached

    db = get_db()
    queries = [AQ.limit(limit), AQ.offset(offset), AQ.order_desc("created_at")]
    if domain:
        queries.append(AQ.equal("domain", domain))
    if is_ai_room is not None:
        queries.append(AQ.equal("is_ai_room", is_ai_room))

    result = db.list_documents(APPWRITE_DATABASE_ID, COLLECTION_DISCUSSIONS, queries)
    await cache_set(cache_key, result, DISCUSSION_CACHE_TTL)
    return result

@app.get("/discussions/{discussion_id}")
async def get_discussion(discussion_id: str):
    cache_key = f"discussion:{discussion_id}"
    cached = await cache_get(cache_key)
    if cached:
        return cached

    db = get_db()
    try:
        doc = db.get_document(APPWRITE_DATABASE_ID, COLLECTION_DISCUSSIONS, discussion_id)
    except Exception:
        raise HTTPException(404, "Discussion not found")
    await cache_set(cache_key, doc, DISCUSSION_CACHE_TTL)
    return doc

@app.put("/discussions/{discussion_id}")
async def update_discussion(discussion_id: str, req: UpdateDiscussionReq, user=Depends(current_user)):
    db = get_db()
    try:
        existing = db.get_document(APPWRITE_DATABASE_ID, COLLECTION_DISCUSSIONS, discussion_id)
    except Exception:
        raise HTTPException(404, "Discussion not found")

    if existing["created_by"] != user["user_id"]:
        raise HTTPException(403, "Not the creator")

    data = {"updated_at": datetime.now(timezone.utc).isoformat()}
    if req.title is not None:
        data["title"] = req.title
    if req.description is not None:
        data["description"] = req.description

    updated = db.update_document(APPWRITE_DATABASE_ID, COLLECTION_DISCUSSIONS, discussion_id, data)
    await cache_delete_pattern(f"discussion:{discussion_id}*")
    await cache_delete_pattern(f"discussions:*")
    return updated

@app.delete("/discussions/{discussion_id}")
async def delete_discussion(discussion_id: str, user=Depends(current_user)):
    db = get_db()
    try:
        existing = db.get_document(APPWRITE_DATABASE_ID, COLLECTION_DISCUSSIONS, discussion_id)
    except Exception:
        raise HTTPException(404, "Discussion not found")

    if existing["created_by"] != user["user_id"]:
        raise HTTPException(403, "Not the creator")

    db.delete_document(APPWRITE_DATABASE_ID, COLLECTION_DISCUSSIONS, discussion_id)
    await cache_delete_pattern(f"discussion:{discussion_id}*")
    await cache_delete_pattern(f"discussions:*")
    return {"deleted": True}

# ── Comments ───────────────────────────────────────────────────────────────
@app.get("/discussions/{discussion_id}/comments")
async def list_comments(
    discussion_id: str,
    limit: int = Query(50, le=100),
    offset: int = 0,
    order: str = "asc",
):
    cache_key = f"comments:{discussion_id}:{limit}:{offset}:{order}"
    cached = await cache_get(cache_key)
    if cached:
        return cached

    db = get_db()
    order_fn = AQ.order_asc if order == "asc" else AQ.order_desc
    queries = [
        AQ.equal("discussion_id", discussion_id),
        AQ.limit(limit),
        AQ.offset(offset),
        order_fn("$createdAt"),
    ]
    result = db.list_documents(APPWRITE_DATABASE_ID, COLLECTION_COMMENTS, queries)
    await cache_set(cache_key, result, COMMENTS_CACHE_TTL)
    return result

@app.post("/discussions/{discussion_id}/comments")
async def add_comment(discussion_id: str, req: CreateCommentReq, user=Depends(current_user)):
    db = get_db()
    # Validate discussion exists
    try:
        disc = db.get_document(APPWRITE_DATABASE_ID, COLLECTION_DISCUSSIONS, discussion_id)
    except Exception:
        raise HTTPException(404, "Discussion not found")

    now = datetime.now(timezone.utc).isoformat()
    doc = db.create_document(
        APPWRITE_DATABASE_ID, COLLECTION_COMMENTS,
        ID.unique(),
        {
            "discussion_id": discussion_id,
            "user_id": user["user_id"],
            "username": user.get("username", ""),
            "avatar_url": user.get("avatar_url", ""),
            "body": req.body,
            "citation_url": req.citation_url,
            "likes_count": 0,
            "created_at": now,
        }
    )
    # Bump count
    db.update_document(
        APPWRITE_DATABASE_ID, COLLECTION_DISCUSSIONS, discussion_id,
        {"comments_count": disc.get("comments_count", 0) + 1, "updated_at": now}
    )
    await cache_delete_pattern(f"comments:{discussion_id}:*")
    await cache_delete_pattern(f"discussion:{discussion_id}")
    return doc

@app.post("/discussions/{discussion_id}/comments/{comment_id}/like")
async def like_comment(discussion_id: str, comment_id: str, user=Depends(current_user)):
    db = get_db()
    try:
        comment = db.get_document(APPWRITE_DATABASE_ID, COLLECTION_COMMENTS, comment_id)
    except Exception:
        raise HTTPException(404, "Comment not found")

    updated = db.update_document(
        APPWRITE_DATABASE_ID, COLLECTION_COMMENTS, comment_id,
        {"likes_count": comment.get("likes_count", 0) + 1}
    )
    await cache_delete_pattern(f"comments:{discussion_id}:*")
    return updated

@app.delete("/discussions/{discussion_id}/comments/{comment_id}")
async def delete_comment(discussion_id: str, comment_id: str, user=Depends(current_user)):
    db = get_db()
    try:
        comment = db.get_document(APPWRITE_DATABASE_ID, COLLECTION_COMMENTS, comment_id)
    except Exception:
        raise HTTPException(404, "Comment not found")

    if comment["user_id"] != user["user_id"]:
        raise HTTPException(403, "Not the author")

    db.delete_document(APPWRITE_DATABASE_ID, COLLECTION_COMMENTS, comment_id)
    await cache_delete_pattern(f"comments:{discussion_id}:*")
    return {"deleted": True}

# ── AI Chat ────────────────────────────────────────────────────────────────
SYSTEM_PROMPT = (
    "You are ScrollU AI — a knowledgeable, engaging discussion facilitator. "
    "You present balanced perspectives, cite reasoning, and encourage critical thinking. "
    "Be concise (2-4 sentences) unless asked to elaborate. Never be preachy or condescending."
)

@app.post("/discussions/ai-chat")
async def ai_chat(req: AIChatReq):
    if not groq_client:
        raise HTTPException(503, "AI service not configured")

    # Build message history
    messages = [{"role": "system", "content": f"{SYSTEM_PROMPT}\n\nTopic: {req.topic} | Domain: {req.domain}"}]
    for h in req.history[-10:]:  # last 10 turns
        role = "assistant" if h.get("role") == "ai" else "user"
        messages.append({"role": role, "content": h.get("content", "")})
    messages.append({"role": "user", "content": req.message})

    try:
        resp = groq_client.chat.completions.create(
            model=GROQ_MODEL_PRIMARY,
            messages=messages,
            max_tokens=400,
            temperature=0.7,
        )
        reply = resp.choices[0].message.content.strip()
    except Exception as e:
        raise HTTPException(500, f"AI error: {e}")

    # Auto-persist AI reply if discussion_id provided
    if req.discussion_id:
        try:
            db = get_db()
            now = datetime.now(timezone.utc).isoformat()
            db.create_document(
                APPWRITE_DATABASE_ID, COLLECTION_COMMENTS, ID.unique(),
                {
                    "discussion_id": req.discussion_id,
                    "user_id": "scrollu_ai",
                    "username": "ScrollU AI",
                    "avatar_url": "",
                    "body": reply,
                    "citation_url": "",
                    "likes_count": 0,
                    "created_at": now,
                }
            )
            try:
                disc = db.get_document(APPWRITE_DATABASE_ID, COLLECTION_DISCUSSIONS, req.discussion_id)
                db.update_document(
                    APPWRITE_DATABASE_ID, COLLECTION_DISCUSSIONS, req.discussion_id,
                    {"comments_count": disc.get("comments_count", 0) + 1, "updated_at": now}
                )
            except Exception:
                pass
            await cache_delete_pattern(f"comments:{req.discussion_id}:*")
        except Exception as e:
            print(f"[AI Chat] Failed to persist reply: {e}")

    return {"reply": reply}

# ── Bias Detection ─────────────────────────────────────────────────────────
BIAS_SYSTEM = (
    "You are a neutral bias detector. Analyze the given text and return a JSON object with:\n"
    "- score: int 0-100 (0=no bias, 100=extreme bias)\n"
    "- flags: list of strings describing detected biases\n"
    "- verdict: one of 'clean', 'mild', 'moderate', 'severe'\n"
    "Return ONLY valid JSON, no extra text."
)

@app.post("/discussions/bias-check")
async def bias_check(req: BiasCheckReq):
    if not groq_client:
        return {"score": 0, "flags": [], "verdict": "clean"}

    try:
        resp = groq_client.chat.completions.create(
            model=GROQ_MODEL_FAST,
            messages=[
                {"role": "system", "content": BIAS_SYSTEM},
                {"role": "user", "content": f"Context: {req.context}\n\nText: {req.text}"},
            ],
            max_tokens=200,
            temperature=0.1,
            response_format={"type": "json_object"},
        )
        import json
        result = json.loads(resp.choices[0].message.content)
        return result
    except Exception as e:
        return {"score": 0, "flags": [], "verdict": "clean", "error": str(e)}

# ── Moderation ─────────────────────────────────────────────────────────────
@app.post("/discussions/{discussion_id}/comments/{comment_id}/report")
async def report_comment(discussion_id: str, comment_id: str, user=Depends(current_user)):
    db = get_db()
    try:
        comment = db.get_document(APPWRITE_DATABASE_ID, COLLECTION_COMMENTS, comment_id)
    except Exception:
        raise HTTPException(404, "Comment not found")

    # Run bias check on the comment body
    bias_result = {"score": 0, "verdict": "clean"}
    if groq_client:
        try:
            resp = groq_client.chat.completions.create(
                model=GROQ_MODEL_FAST,
                messages=[
                    {"role": "system", "content": BIAS_SYSTEM},
                    {"role": "user", "content": f"Text: {comment['body']}"},
                ],
                max_tokens=200, temperature=0.1,
                response_format={"type": "json_object"},
            )
            import json
            bias_result = json.loads(resp.choices[0].message.content)
        except Exception:
            pass

    now = datetime.now(timezone.utc).isoformat()
    db.create_document(
        APPWRITE_DATABASE_ID, COLLECTION_USER_VIOLATIONS, ID.unique(),
        {
            "reported_user_id": comment["user_id"],
            "reported_by": user["user_id"],
            "comment_id": comment_id,
            "discussion_id": discussion_id,
            "comment_body": comment["body"],
            "bias_score": bias_result.get("score", 0),
            "bias_verdict": bias_result.get("verdict", "clean"),
            "resolved": False,
            "created_at": now,
        }
    )
    return {"reported": True, "bias_score": bias_result.get("score", 0)}

# ── User discussion history ────────────────────────────────────────────────
@app.get("/discussions/user/{user_id}/history")
async def get_user_history(user_id: str, limit: int = Query(20, le=50)):
    db = get_db()
    # Get all comments by this user
    user_comments = db.list_documents(
        APPWRITE_DATABASE_ID, COLLECTION_COMMENTS,
        [AQ.equal("user_id", user_id), AQ.order_desc("$createdAt"), AQ.limit(200)]
    )

    # Unique discussion IDs (preserve order)
    seen = set()
    disc_ids = []
    for c in user_comments["documents"]:
        did = c.get("discussion_id", "")
        if did and did not in seen:
            seen.add(did)
            disc_ids.append(did)
        if len(disc_ids) >= limit:
            break

    history = []
    for disc_id in disc_ids:
        try:
            disc = db.get_document(APPWRITE_DATABASE_ID, COLLECTION_DISCUSSIONS, disc_id)
            thread = db.list_documents(
                APPWRITE_DATABASE_ID, COLLECTION_COMMENTS,
                [AQ.equal("discussion_id", disc_id), AQ.order_asc("$createdAt"), AQ.limit(100)]
            )
            history.append({"discussion": disc, "messages": thread["documents"]})
        except Exception:
            continue

    return {"total": len(history), "items": history}

# ── Health ─────────────────────────────────────────────────────────────────
@app.get("/discussions/health")
async def health():
    return {"status": "ok", "service": "discussion", "port": 8003}
