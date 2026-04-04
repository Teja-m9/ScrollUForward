"""User Service — port 8004
Handles user profiles, follow/unfollow, leaderboard, XP/badges, bookmarks.
"""
from __future__ import annotations
import os, sys
from datetime import datetime, timezone
from typing import Optional, List

from fastapi import FastAPI, HTTPException, Header, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))
from microservices.shared.config import (
    APPWRITE_DATABASE_ID, COLLECTION_USERS, COLLECTION_CONTENT,
    COLLECTION_INTERACTIONS,
)
from microservices.shared.appwrite_client import get_db
from microservices.shared.redis_client import (
    cache_get, cache_set, cache_delete, cache_delete_pattern,
    key_user, key_leaderboard,
)
from microservices.shared.auth import decode_token
from appwrite.id import ID
from appwrite.query import Query as AQ

# ── App ────────────────────────────────────────────────────────────────────
app = FastAPI(title="User Service", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

USER_CACHE_TTL        = 300   # 5 min
LEADERBOARD_CACHE_TTL = 120   # 2 min

# XP constants
XP_COMMENT   = 5
XP_LIKE      = 2
XP_SHARE     = 3
XP_WATCH     = 10
XP_DAILY     = 20

BADGE_THRESHOLDS = {
    "newcomer":   0,
    "curious":    100,
    "explorer":   300,
    "scholar":    700,
    "sage":       1500,
    "legend":     3000,
}

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
class UpdateProfileReq(BaseModel):
    username: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    interest_tags: Optional[List[str]] = None
    location: Optional[str] = None
    website: Optional[str] = None

class GrantXPReq(BaseModel):
    user_id: str
    xp_type: str  # comment, like, share, watch, daily
    amount: Optional[int] = None

# ── Profile ────────────────────────────────────────────────────────────────
@app.get("/users/{user_id}")
async def get_profile(user_id: str, me=Depends(optional_user)):
    cache_key = key_user(user_id)
    cached = await cache_get(cache_key)
    if cached:
        return cached

    db = get_db()
    results = db.list_documents(
        APPWRITE_DATABASE_ID, COLLECTION_USERS,
        [AQ.equal("user_id", user_id), AQ.limit(1)]
    )
    if not results["documents"]:
        raise HTTPException(404, "User not found")

    doc = results["documents"][0]
    # Strip sensitive fields for non-self views
    if not me or me.get("user_id") != user_id:
        doc.pop("email", None)
        doc.pop("password_hash", None)

    await cache_set(cache_key, doc, USER_CACHE_TTL)
    return doc

@app.put("/users/{user_id}")
async def update_profile(user_id: str, req: UpdateProfileReq, user=Depends(current_user)):
    if user["user_id"] != user_id:
        raise HTTPException(403, "Cannot edit another user's profile")

    db = get_db()
    results = db.list_documents(
        APPWRITE_DATABASE_ID, COLLECTION_USERS,
        [AQ.equal("user_id", user_id), AQ.limit(1)]
    )
    if not results["documents"]:
        raise HTTPException(404, "User not found")

    doc_id = results["documents"][0]["$id"]
    data = {"updated_at": datetime.now(timezone.utc).isoformat()}
    if req.username is not None:
        data["username"] = req.username
    if req.bio is not None:
        data["bio"] = req.bio
    if req.avatar_url is not None:
        data["avatar_url"] = req.avatar_url
    if req.interest_tags is not None:
        data["interest_tags"] = req.interest_tags
    if req.location is not None:
        data["location"] = req.location
    if req.website is not None:
        data["website"] = req.website

    updated = db.update_document(APPWRITE_DATABASE_ID, COLLECTION_USERS, doc_id, data)
    await cache_delete(key_user(user_id))
    return updated

@app.get("/users/")
async def search_users(q: str = Query(..., min_length=2), limit: int = Query(10, le=20)):
    db = get_db()
    results = db.list_documents(
        APPWRITE_DATABASE_ID, COLLECTION_USERS,
        [AQ.search("username", q), AQ.limit(limit)]
    )
    # Strip sensitive fields
    for doc in results["documents"]:
        doc.pop("email", None)
        doc.pop("password_hash", None)
    return results

# ── Follow / Unfollow ──────────────────────────────────────────────────────
COLLECTION_FOLLOWS = "follows"

@app.post("/users/{user_id}/follow")
async def follow_user(user_id: str, me=Depends(current_user)):
    if me["user_id"] == user_id:
        raise HTTPException(400, "Cannot follow yourself")

    db = get_db()
    # Check if already following
    existing = db.list_documents(
        APPWRITE_DATABASE_ID, COLLECTION_FOLLOWS,
        [AQ.equal("follower_id", me["user_id"]), AQ.equal("following_id", user_id), AQ.limit(1)]
    )
    if existing["documents"]:
        raise HTTPException(409, "Already following")

    now = datetime.now(timezone.utc).isoformat()
    db.create_document(
        APPWRITE_DATABASE_ID, COLLECTION_FOLLOWS, ID.unique(),
        {"follower_id": me["user_id"], "following_id": user_id, "created_at": now}
    )
    # Update follower/following counts
    _bump_follow_counts(db, me["user_id"], user_id, +1)
    await cache_delete(key_user(user_id))
    await cache_delete(key_user(me["user_id"]))
    return {"following": True}

@app.delete("/users/{user_id}/follow")
async def unfollow_user(user_id: str, me=Depends(current_user)):
    db = get_db()
    existing = db.list_documents(
        APPWRITE_DATABASE_ID, COLLECTION_FOLLOWS,
        [AQ.equal("follower_id", me["user_id"]), AQ.equal("following_id", user_id), AQ.limit(1)]
    )
    if not existing["documents"]:
        raise HTTPException(404, "Not following")

    db.delete_document(APPWRITE_DATABASE_ID, COLLECTION_FOLLOWS, existing["documents"][0]["$id"])
    _bump_follow_counts(db, me["user_id"], user_id, -1)
    await cache_delete(key_user(user_id))
    await cache_delete(key_user(me["user_id"]))
    return {"following": False}

@app.get("/users/{user_id}/followers")
async def get_followers(user_id: str, limit: int = Query(20, le=50), offset: int = 0):
    db = get_db()
    follows = db.list_documents(
        APPWRITE_DATABASE_ID, COLLECTION_FOLLOWS,
        [AQ.equal("following_id", user_id), AQ.limit(limit), AQ.offset(offset), AQ.order_desc("created_at")]
    )
    return {"total": follows["total"], "follower_ids": [f["follower_id"] for f in follows["documents"]]}

@app.get("/users/{user_id}/following")
async def get_following(user_id: str, limit: int = Query(20, le=50), offset: int = 0):
    db = get_db()
    follows = db.list_documents(
        APPWRITE_DATABASE_ID, COLLECTION_FOLLOWS,
        [AQ.equal("follower_id", user_id), AQ.limit(limit), AQ.offset(offset), AQ.order_desc("created_at")]
    )
    return {"total": follows["total"], "following_ids": [f["following_id"] for f in follows["documents"]]}

def _bump_follow_counts(db, follower_id: str, following_id: str, delta: int):
    """Increment/decrement followers_count and following_count."""
    for uid, field in [(follower_id, "following_count"), (following_id, "followers_count")]:
        try:
            res = db.list_documents(
                APPWRITE_DATABASE_ID, COLLECTION_USERS,
                [AQ.equal("user_id", uid), AQ.limit(1)]
            )
            if res["documents"]:
                doc = res["documents"][0]
                current = doc.get(field, 0)
                db.update_document(
                    APPWRITE_DATABASE_ID, COLLECTION_USERS, doc["$id"],
                    {field: max(0, current + delta)}
                )
        except Exception as e:
            print(f"[User] Failed to update {field} for {uid}: {e}")

# ── XP & Badges ────────────────────────────────────────────────────────────
def _compute_badge(xp: int) -> str:
    badge = "newcomer"
    for name, threshold in BADGE_THRESHOLDS.items():
        if xp >= threshold:
            badge = name
    return badge

@app.post("/users/xp/grant")
async def grant_xp(req: GrantXPReq):
    """Internal endpoint called by other services to award XP."""
    xp_map = {
        "comment": XP_COMMENT,
        "like": XP_LIKE,
        "share": XP_SHARE,
        "watch": XP_WATCH,
        "daily": XP_DAILY,
    }
    xp_amount = req.amount if req.amount else xp_map.get(req.xp_type, 0)
    if xp_amount == 0:
        return {"granted": 0}

    db = get_db()
    results = db.list_documents(
        APPWRITE_DATABASE_ID, COLLECTION_USERS,
        [AQ.equal("user_id", req.user_id), AQ.limit(1)]
    )
    if not results["documents"]:
        raise HTTPException(404, "User not found")

    doc = results["documents"][0]
    new_xp = doc.get("xp", 0) + xp_amount
    new_badge = _compute_badge(new_xp)

    db.update_document(
        APPWRITE_DATABASE_ID, COLLECTION_USERS, doc["$id"],
        {"xp": new_xp, "badge": new_badge, "updated_at": datetime.now(timezone.utc).isoformat()}
    )
    await cache_delete(key_user(req.user_id))
    await cache_delete(key_leaderboard())
    return {"granted": xp_amount, "total_xp": new_xp, "badge": new_badge}

@app.get("/users/{user_id}/badges")
async def get_badges(user_id: str):
    db = get_db()
    results = db.list_documents(
        APPWRITE_DATABASE_ID, COLLECTION_USERS,
        [AQ.equal("user_id", user_id), AQ.limit(1)]
    )
    if not results["documents"]:
        raise HTTPException(404, "User not found")

    doc = results["documents"][0]
    xp = doc.get("xp", 0)
    current_badge = _compute_badge(xp)
    earned = [name for name, threshold in BADGE_THRESHOLDS.items() if xp >= threshold]
    next_badges = [(name, threshold) for name, threshold in BADGE_THRESHOLDS.items() if xp < threshold]
    next_up = next_badges[0] if next_badges else None

    return {
        "xp": xp,
        "current_badge": current_badge,
        "earned_badges": earned,
        "next_badge": next_up[0] if next_up else None,
        "xp_to_next": (next_up[1] - xp) if next_up else 0,
    }

# ── Leaderboard ────────────────────────────────────────────────────────────
@app.get("/users/leaderboard/global")
async def global_leaderboard(limit: int = Query(20, le=50)):
    cache_key = key_leaderboard()
    cached = await cache_get(cache_key)
    if cached:
        return cached

    db = get_db()
    results = db.list_documents(
        APPWRITE_DATABASE_ID, COLLECTION_USERS,
        [AQ.order_desc("xp"), AQ.limit(limit)]
    )
    board = []
    for i, doc in enumerate(results["documents"]):
        board.append({
            "rank": i + 1,
            "user_id": doc["user_id"],
            "username": doc.get("username", ""),
            "avatar_url": doc.get("avatar_url", ""),
            "xp": doc.get("xp", 0),
            "badge": doc.get("badge", "newcomer"),
        })

    result = {"leaderboard": board}
    await cache_set(cache_key, result, LEADERBOARD_CACHE_TTL)
    return result

@app.get("/users/{user_id}/rank")
async def user_rank(user_id: str):
    db = get_db()
    # Get user XP
    results = db.list_documents(
        APPWRITE_DATABASE_ID, COLLECTION_USERS,
        [AQ.equal("user_id", user_id), AQ.limit(1)]
    )
    if not results["documents"]:
        raise HTTPException(404, "User not found")
    user_xp = results["documents"][0].get("xp", 0)

    # Count users with higher XP
    above = db.list_documents(
        APPWRITE_DATABASE_ID, COLLECTION_USERS,
        [AQ.greater_than("xp", user_xp)]
    )
    rank = above["total"] + 1
    return {"user_id": user_id, "rank": rank, "xp": user_xp}

# ── Bookmarks ──────────────────────────────────────────────────────────────
COLLECTION_BOOKMARKS = "bookmarks"

@app.get("/users/{user_id}/bookmarks")
async def get_bookmarks(user_id: str, me=Depends(current_user), limit: int = Query(20, le=50), offset: int = 0):
    if me["user_id"] != user_id:
        raise HTTPException(403, "Cannot view another user's bookmarks")

    db = get_db()
    results = db.list_documents(
        APPWRITE_DATABASE_ID, COLLECTION_BOOKMARKS,
        [AQ.equal("user_id", user_id), AQ.order_desc("created_at"), AQ.limit(limit), AQ.offset(offset)]
    )
    return results

@app.post("/users/{user_id}/bookmarks/{content_id}")
async def add_bookmark(user_id: str, content_id: str, me=Depends(current_user)):
    if me["user_id"] != user_id:
        raise HTTPException(403, "Forbidden")

    db = get_db()
    existing = db.list_documents(
        APPWRITE_DATABASE_ID, COLLECTION_BOOKMARKS,
        [AQ.equal("user_id", user_id), AQ.equal("content_id", content_id), AQ.limit(1)]
    )
    if existing["documents"]:
        raise HTTPException(409, "Already bookmarked")

    doc = db.create_document(
        APPWRITE_DATABASE_ID, COLLECTION_BOOKMARKS, ID.unique(),
        {"user_id": user_id, "content_id": content_id, "created_at": datetime.now(timezone.utc).isoformat()}
    )
    return doc

@app.delete("/users/{user_id}/bookmarks/{content_id}")
async def remove_bookmark(user_id: str, content_id: str, me=Depends(current_user)):
    if me["user_id"] != user_id:
        raise HTTPException(403, "Forbidden")

    db = get_db()
    existing = db.list_documents(
        APPWRITE_DATABASE_ID, COLLECTION_BOOKMARKS,
        [AQ.equal("user_id", user_id), AQ.equal("content_id", content_id), AQ.limit(1)]
    )
    if not existing["documents"]:
        raise HTTPException(404, "Bookmark not found")

    db.delete_document(APPWRITE_DATABASE_ID, COLLECTION_BOOKMARKS, existing["documents"][0]["$id"])
    return {"removed": True}

# ── Activity ───────────────────────────────────────────────────────────────
@app.get("/users/{user_id}/activity")
async def get_activity(user_id: str, limit: int = Query(20, le=50), offset: int = 0):
    db = get_db()
    results = db.list_documents(
        APPWRITE_DATABASE_ID, COLLECTION_INTERACTIONS,
        [AQ.equal("user_id", user_id), AQ.order_desc("$createdAt"), AQ.limit(limit), AQ.offset(offset)]
    )
    return results

# ── Streak tracking ────────────────────────────────────────────────────────
@app.post("/users/{user_id}/check-in")
async def daily_check_in(user_id: str, me=Depends(current_user)):
    if me["user_id"] != user_id:
        raise HTTPException(403, "Forbidden")

    db = get_db()
    results = db.list_documents(
        APPWRITE_DATABASE_ID, COLLECTION_USERS,
        [AQ.equal("user_id", user_id), AQ.limit(1)]
    )
    if not results["documents"]:
        raise HTTPException(404, "User not found")

    doc = results["documents"][0]
    now = datetime.now(timezone.utc)
    last_checkin_str = doc.get("last_checkin_at", "")

    already_checked_in = False
    streak = doc.get("streak", 0)
    if last_checkin_str:
        last = datetime.fromisoformat(last_checkin_str.replace("Z", "+00:00"))
        diff_hours = (now - last).total_seconds() / 3600
        if diff_hours < 24:
            already_checked_in = True
        elif diff_hours < 48:
            streak += 1  # continued streak
        else:
            streak = 1   # broken streak

    if already_checked_in:
        return {"checked_in": False, "streak": streak, "message": "Already checked in today"}

    new_xp = doc.get("xp", 0) + XP_DAILY
    new_badge = _compute_badge(new_xp)
    db.update_document(
        APPWRITE_DATABASE_ID, COLLECTION_USERS, doc["$id"],
        {
            "xp": new_xp, "badge": new_badge, "streak": streak,
            "last_checkin_at": now.isoformat(), "updated_at": now.isoformat()
        }
    )
    await cache_delete(key_user(user_id))
    await cache_delete(key_leaderboard())
    return {"checked_in": True, "streak": streak, "xp_gained": XP_DAILY, "total_xp": new_xp, "badge": new_badge}

# ── Health ─────────────────────────────────────────────────────────────────
@app.get("/users/health")
async def health():
    return {"status": "ok", "service": "user", "port": 8004}
