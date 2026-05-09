import json
import logging
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, Depends
from appwrite.query import Query
from appwrite.id import ID
from auth import get_current_user
from appwrite_client import get_databases
from schemas import IQUpdate, LeaderboardEntry, UpdateProfileRequest
from config import (
    APPWRITE_DATABASE_ID, COLLECTION_USERS, COLLECTION_INTERACTIONS,
    COLLECTION_CONTENT, IQ_POINTS,
)
from cache import cached, cache_invalidate

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["Users & IQ"])


@router.put("/profile")
async def update_profile(update: UpdateProfileRequest, current_user: dict = Depends(get_current_user)):
    db = get_databases()
    data = {}
    if update.display_name is not None:
        data["display_name"] = update.display_name
    if update.bio is not None:
        data["bio"] = update.bio
    if update.avatar_url is not None:
        data["avatar_url"] = update.avatar_url
    if update.interest_tags is not None:
        data["interest_tags"] = json.dumps(update.interest_tags)

    if not data:
        raise HTTPException(status_code=400, detail="No fields to update")

    try:
        doc = db.update_document(
            database_id=APPWRITE_DATABASE_ID,
            collection_id=COLLECTION_USERS,
            document_id=current_user["sub"],
            data=data
        )
        return {"status": "updated", "user_id": doc["$id"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/iq/earn")
async def earn_iq_points(iq_update: IQUpdate, current_user: dict = Depends(get_current_user)):
    db = get_databases()

    points = IQ_POINTS.get(iq_update.action, 0)
    if points == 0:
        raise HTTPException(status_code=400, detail=f"Unknown action: {iq_update.action}")

    try:
        user = db.get_document(
            database_id=APPWRITE_DATABASE_ID,
            collection_id=COLLECTION_USERS,
            document_id=current_user["sub"]
        )
        new_score = user.get("iq_score", 0) + points
        new_rank = _calculate_rank(new_score)

        db.update_document(
            database_id=APPWRITE_DATABASE_ID,
            collection_id=COLLECTION_USERS,
            document_id=current_user["sub"],
            data={
                "iq_score": new_score,
                "knowledge_rank": new_rank,
            }
        )

        # Log the interaction
        if iq_update.content_id:
            db.create_document(
                database_id=APPWRITE_DATABASE_ID,
                collection_id=COLLECTION_INTERACTIONS,
                document_id=ID.unique(),
                data={
                    "user_id": current_user["sub"],
                    "content_id": iq_update.content_id,
                    "interaction_type": iq_update.action,
                }
            )

        # Bust caches that include this user's stats / leaderboard rank
        await cache_invalidate(f"user:{current_user['sub']}:stats", "leaderboard:*")

        return {
            "points_earned": points,
            "new_total": new_score,
            "rank": new_rank,
            "action": iq_update.action,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/leaderboard", response_model=list[LeaderboardEntry])
@cached(ttl=60, key_fn=lambda limit=20: f"leaderboard:{limit}")
async def get_leaderboard(limit: int = 20):
    db = get_databases()
    try:
        result = db.list_documents(
            database_id=APPWRITE_DATABASE_ID,
            collection_id=COLLECTION_USERS,
            queries=[
                Query.order_desc("iq_score"),
                Query.limit(limit),
            ]
        )
        entries = []
        for i, doc in enumerate(result["documents"]):
            entries.append(LeaderboardEntry(
                user_id=doc["$id"],
                username=doc.get("username", ""),
                display_name=doc.get("display_name", ""),
                avatar_url=doc.get("avatar_url", ""),
                iq_score=doc.get("iq_score", 0),
                knowledge_rank=doc.get("knowledge_rank", "Novice"),
                rank_position=i + 1,
            ))
        return entries
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{user_id}")
@cached(ttl=30, key_fn=lambda user_id: f"user:{user_id}:profile")
async def get_user_profile(user_id: str):
    db = get_databases()
    try:
        user = db.get_document(
            database_id=APPWRITE_DATABASE_ID,
            collection_id=COLLECTION_USERS,
            document_id=user_id
        )
        return {
            "user_id": user["$id"],
            "username": user.get("username", ""),
            "display_name": user.get("display_name", ""),
            "bio": user.get("bio", ""),
            "avatar_url": user.get("avatar_url", ""),
            "iq_score": user.get("iq_score", 0),
            "knowledge_rank": user.get("knowledge_rank", "Novice"),
            "interest_tags": json.loads(user.get("interest_tags", "[]")),
            "followers_count": user.get("followers_count", 0),
            "following_count": user.get("following_count", 0),
            "posts_count": user.get("posts_count", 0),
            "streak_days": user.get("streak_days", 0),
            "badges": json.loads(user.get("badges", "[]")),
        }
    except Exception:
        raise HTTPException(status_code=404, detail="User not found")


@router.post("/{user_id}/follow")
async def follow_user(user_id: str, current_user: dict = Depends(get_current_user)):
    db = get_databases()
    me_id = current_user["sub"]
    if user_id == me_id:
        raise HTTPException(status_code=400, detail="Cannot follow yourself")

    try:
        # Already following? Idempotent — don't double-count
        existing = db.list_documents(
            database_id=APPWRITE_DATABASE_ID,
            collection_id=COLLECTION_INTERACTIONS,
            queries=[
                Query.equal("user_id", me_id),
                Query.equal("content_id", user_id),
                Query.equal("interaction_type", "follow"),
                Query.limit(1),
            ],
        )
        if (existing.get("total") or 0) > 0:
            return {"status": "already_following", "user_id": user_id}

        # Record the follow as an interaction (so we can query who-follows-whom)
        db.create_document(
            database_id=APPWRITE_DATABASE_ID,
            collection_id=COLLECTION_INTERACTIONS,
            document_id=ID.unique(),
            data={
                "user_id": me_id,
                "content_id": user_id,
                "interaction_type": "follow",
            },
        )

        # Bump cached counts
        target = db.get_document(
            database_id=APPWRITE_DATABASE_ID,
            collection_id=COLLECTION_USERS,
            document_id=user_id,
        )
        db.update_document(
            database_id=APPWRITE_DATABASE_ID,
            collection_id=COLLECTION_USERS,
            document_id=user_id,
            data={"followers_count": target.get("followers_count", 0) + 1},
        )
        me = db.get_document(
            database_id=APPWRITE_DATABASE_ID,
            collection_id=COLLECTION_USERS,
            document_id=me_id,
        )
        db.update_document(
            database_id=APPWRITE_DATABASE_ID,
            collection_id=COLLECTION_USERS,
            document_id=me_id,
            data={"following_count": me.get("following_count", 0) + 1},
        )
        # Invalidate caches that include the new follow relationship
        await cache_invalidate(
            f"user:{user_id}:followers",
            f"user:{user_id}:profile",
            f"user:{me_id}:following",
            f"user:{me_id}:profile",
        )
        return {"status": "followed", "user_id": user_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{user_id}/follow")
async def unfollow_user(user_id: str, current_user: dict = Depends(get_current_user)):
    db = get_databases()
    me_id = current_user["sub"]
    if user_id == me_id:
        raise HTTPException(status_code=400, detail="Cannot unfollow yourself")

    try:
        existing = db.list_documents(
            database_id=APPWRITE_DATABASE_ID,
            collection_id=COLLECTION_INTERACTIONS,
            queries=[
                Query.equal("user_id", me_id),
                Query.equal("content_id", user_id),
                Query.equal("interaction_type", "follow"),
                Query.limit(5),
            ],
        )
        if (existing.get("total") or 0) == 0:
            return {"status": "not_following", "user_id": user_id}

        for doc in existing.get("documents", []):
            try:
                db.delete_document(
                    database_id=APPWRITE_DATABASE_ID,
                    collection_id=COLLECTION_INTERACTIONS,
                    document_id=doc["$id"],
                )
            except Exception:
                pass

        target = db.get_document(
            database_id=APPWRITE_DATABASE_ID,
            collection_id=COLLECTION_USERS,
            document_id=user_id,
        )
        db.update_document(
            database_id=APPWRITE_DATABASE_ID,
            collection_id=COLLECTION_USERS,
            document_id=user_id,
            data={"followers_count": max(0, target.get("followers_count", 0) - 1)},
        )
        me = db.get_document(
            database_id=APPWRITE_DATABASE_ID,
            collection_id=COLLECTION_USERS,
            document_id=me_id,
        )
        db.update_document(
            database_id=APPWRITE_DATABASE_ID,
            collection_id=COLLECTION_USERS,
            document_id=me_id,
            data={"following_count": max(0, me.get("following_count", 0) - 1)},
        )
        await cache_invalidate(
            f"user:{user_id}:followers",
            f"user:{user_id}:profile",
            f"user:{me_id}:following",
            f"user:{me_id}:profile",
        )
        return {"status": "unfollowed", "user_id": user_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _calculate_rank(iq_score: int) -> str:
    if iq_score >= 5000:
        return "Grandmaster"
    elif iq_score >= 2500:
        return "Master"
    elif iq_score >= 1000:
        return "Expert"
    elif iq_score >= 500:
        return "Scholar"
    elif iq_score >= 100:
        return "Learner"
    else:
        return "Novice"


# ─── Live profile extras ─────────────────────────────────────
DAILY_GOAL_TARGET = 10  # interactions/day to hit 100%

BADGE_RULES = [
    ("first_step",   "First Step",     "footsteps-outline", lambda iq, posts, streak, ints: ints >= 1),
    ("curious_mind", "Curious Mind",   "bulb-outline",      lambda iq, posts, streak, ints: ints >= 25),
    ("scholar",      "Scholar",        "school-outline",    lambda iq, posts, streak, ints: iq >= 500),
    ("creator",      "Creator",        "create-outline",    lambda iq, posts, streak, ints: posts >= 5),
    ("week_warrior", "Week Warrior",   "flame-outline",     lambda iq, posts, streak, ints: streak >= 7),
    ("month_legend", "Month Legend",   "trophy-outline",    lambda iq, posts, streak, ints: streak >= 30),
    ("expert",       "Expert",         "ribbon-outline",    lambda iq, posts, streak, ints: iq >= 1000),
    ("master",       "Master",         "medal-outline",     lambda iq, posts, streak, ints: iq >= 2500),
]


def _list_follow_interactions(db, *, follower_id=None, target_id=None, limit=200):
    """Helper: list 'follow' interactions filtered by follower or target."""
    queries = [Query.equal("interaction_type", "follow"), Query.limit(limit)]
    if follower_id is not None:
        queries.append(Query.equal("user_id", follower_id))
    if target_id is not None:
        queries.append(Query.equal("content_id", target_id))
    try:
        return db.list_documents(
            database_id=APPWRITE_DATABASE_ID,
            collection_id=COLLECTION_INTERACTIONS,
            queries=queries,
        ).get("documents", []) or []
    except Exception:
        return []


def _hydrate_user(db, uid: str) -> dict:
    try:
        u = db.get_document(
            database_id=APPWRITE_DATABASE_ID,
            collection_id=COLLECTION_USERS,
            document_id=uid,
        )
        return {
            "user_id": uid,
            "username": u.get("username", ""),
            "display_name": u.get("display_name", "") or u.get("username", ""),
            "avatar_url": u.get("avatar_url", ""),
            "iq_score": u.get("iq_score", 0),
            "knowledge_rank": u.get("knowledge_rank", "Novice"),
        }
    except Exception:
        return {"user_id": uid, "username": "", "display_name": uid[:8], "avatar_url": "", "iq_score": 0, "knowledge_rank": "Novice"}


@router.get("/{user_id}/stats")
@cached(ttl=30, key_fn=lambda user_id: f"user:{user_id}:stats")
async def get_user_stats(user_id: str):
    """Real-time stats: streak, daily-goal %, rank, badges. Computed live from
    interactions and content collections — not cached fields."""
    db = get_databases()
    try:
        u = db.get_document(
            database_id=APPWRITE_DATABASE_ID,
            collection_id=COLLECTION_USERS,
            document_id=user_id,
        )
    except Exception:
        raise HTTPException(status_code=404, detail="User not found")

    iq = u.get("iq_score", 0)

    # Pull this user's interactions (last 500, capped) for streak + daily goal
    try:
        ir = db.list_documents(
            database_id=APPWRITE_DATABASE_ID,
            collection_id=COLLECTION_INTERACTIONS,
            queries=[Query.equal("user_id", user_id), Query.limit(500)],
        )
        interactions = ir.get("documents", []) or []
    except Exception:
        interactions = []

    # Streak: number of consecutive days ending today with at least 1 interaction
    today = datetime.utcnow().date()
    days_with_activity = set()
    for ia in interactions:
        ts = ia.get("$createdAt")
        if not ts:
            continue
        try:
            d = datetime.fromisoformat(ts.replace("Z", "+00:00")).date()
            days_with_activity.add(d)
        except Exception:
            continue
    streak = 0
    cursor = today
    while cursor in days_with_activity:
        streak += 1
        cursor = cursor - timedelta(days=1)

    # Daily goal: today's interaction count vs target
    today_count = sum(
        1 for ia in interactions
        if (ia.get("$createdAt") or "").startswith(today.isoformat())
    )
    daily_goal_pct = min(100, int((today_count / DAILY_GOAL_TARGET) * 100))

    # User's posts count (live)
    try:
        pr = db.list_documents(
            database_id=APPWRITE_DATABASE_ID,
            collection_id=COLLECTION_CONTENT,
            queries=[Query.equal("author_id", user_id), Query.limit(200)],
        )
        post_docs = pr.get("documents", []) or []
        # Posts only (exclude stories)
        posts_count = sum(1 for p in post_docs if (p.get("content_type") or "") != "story")
    except Exception:
        posts_count = u.get("posts_count", 0)

    rank = _calculate_rank(iq)

    # Compute badges live from rules
    earned_badges = []
    total_ints = len(interactions)
    for key, label, icon, rule in BADGE_RULES:
        try:
            if rule(iq, posts_count, streak, total_ints):
                earned_badges.append({"key": key, "label": label, "icon": icon})
        except Exception:
            continue

    return {
        "user_id": user_id,
        "iq_score": iq,
        "rank": rank,
        "streak_days": streak,
        "today_actions": today_count,
        "daily_goal_target": DAILY_GOAL_TARGET,
        "daily_goal_pct": daily_goal_pct,
        "total_interactions": total_ints,
        "posts_count": posts_count,
        "badges": earned_badges,
    }


@router.get("/{user_id}/followers")
@cached(ttl=60, key_fn=lambda user_id: f"user:{user_id}:followers")
async def list_followers(user_id: str):
    """Return the actual users who follow this user, with profile info."""
    db = get_databases()
    docs = _list_follow_interactions(db, target_id=user_id, limit=200)
    follower_ids = list({d.get("user_id") for d in docs if d.get("user_id")})
    profiles = [_hydrate_user(db, uid) for uid in follower_ids]
    return {
        "count": len(profiles),
        "items": profiles,
        # legacy fields for older client builds
        "follower_ids": follower_ids,
    }


@router.get("/{user_id}/following")
@cached(ttl=60, key_fn=lambda user_id: f"user:{user_id}:following")
async def list_following(user_id: str):
    """Return the actual users this user follows, with profile info."""
    db = get_databases()
    docs = _list_follow_interactions(db, follower_id=user_id, limit=200)
    following_ids = list({d.get("content_id") for d in docs if d.get("content_id")})
    profiles = [_hydrate_user(db, uid) for uid in following_ids]
    return {
        "count": len(profiles),
        "items": profiles,
        "following_ids": following_ids,
    }


@router.get("/{user_id}/posts")
@cached(ttl=30, key_fn=lambda user_id, limit=50: f"user:{user_id}:posts:{limit}")
async def list_user_posts(user_id: str, limit: int = 50):
    """Return only this user's posts (no stories)."""
    db = get_databases()
    try:
        pr = db.list_documents(
            database_id=APPWRITE_DATABASE_ID,
            collection_id=COLLECTION_CONTENT,
            queries=[
                Query.equal("author_id", user_id),
                Query.order_desc("$createdAt"),
                Query.limit(limit),
            ],
        )
        items = pr.get("documents", []) or []
        out = []
        for p in items:
            if (p.get("content_type") or "") == "story":
                continue   # exclude stories from the posts grid
            out.append({
                "id": p["$id"],
                "title": p.get("title", ""),
                "body": p.get("body", ""),
                "content_type": p.get("content_type", "reel"),
                "domain": p.get("domain", ""),
                "thumbnail_url": p.get("thumbnail_url", ""),
                "media_url": p.get("media_url", ""),
                "author_id": p.get("author_id", ""),
                "author_username": p.get("author_username", ""),
                "likes_count": p.get("likes_count", 0),
                "saves_count": p.get("saves_count", 0),
                "comments_count": p.get("comments_count", 0),
                "views_count": p.get("views_count", 0),
                "created_at": p.get("$createdAt", ""),
            })
        return out
    except Exception as e:
        logger.warning(f"list_user_posts failed: {e}")
        return []
