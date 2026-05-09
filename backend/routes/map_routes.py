"""
Map API — Real-time user locations for the nearby/friends map screen.
Locations are stored in Redis (Stage 1 migration) and expire after LOCATION_TTL.
Falls back to a per-process in-memory dict when Redis is unavailable.
"""
import json
import time
import logging
from collections import defaultdict
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Dict

from appwrite.query import Query
from auth import get_current_user
from appwrite_client import get_databases
from config import (
    APPWRITE_DATABASE_ID, COLLECTION_USERS,
    COLLECTION_INTERACTIONS, COLLECTION_CONTENT, DOMAINS,
)
from cache import cached, get_redis

KNOWN_DOMAINS = set(DOMAINS)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/map", tags=["Map"])

LOCATION_TTL = 600  # 10 minutes — a user is "live" on the map for this long
REDIS_HASH = "map:loc"

# Per-process fallback when Redis is unreachable
_locations: Dict[str, dict] = {}


async def _set_location(uid: str, data: dict):
    r = await get_redis()
    if r is None:
        _locations[uid] = data
        return
    await r.hset(REDIS_HASH, uid, json.dumps(data))


async def _delete_location(uid: str):
    r = await get_redis()
    if r is None:
        _locations.pop(uid, None)
        return
    try:
        await r.hdel(REDIS_HASH, uid)
    except Exception:
        pass


async def _get_all_locations() -> Dict[str, dict]:
    """Return {uid: {lat, lng, updated_at}} for all live users.
    Lazily prunes entries older than LOCATION_TTL."""
    r = await get_redis()
    now = time.time()
    out: Dict[str, dict] = {}

    if r is None:
        # In-memory path
        expired = [uid for uid, v in _locations.items() if now - v["updated_at"] > LOCATION_TTL]
        for uid in expired:
            _locations.pop(uid, None)
        return dict(_locations)

    try:
        raw = await r.hgetall(REDIS_HASH)
    except Exception as e:
        logger.warning(f"map: hgetall failed, falling back to memory: {e}")
        return dict(_locations)

    expired_uids = []
    for uid, raw_json in (raw or {}).items():
        try:
            v = json.loads(raw_json)
            if now - v.get("updated_at", 0) > LOCATION_TTL:
                expired_uids.append(uid)
                continue
            out[uid] = v
        except Exception:
            expired_uids.append(uid)

    if expired_uids:
        try:
            await r.hdel(REDIS_HASH, *expired_uids)
        except Exception:
            pass
    return out


class LocationUpdate(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)


class NearbyUser(BaseModel):
    user_id: str
    username: str
    display_name: str
    avatar_url: str
    latitude: float
    longitude: float
    seconds_ago: int
    is_me: bool = False


@router.post("/location")
async def update_my_location(loc: LocationUpdate, current_user: dict = Depends(get_current_user)):
    """Called periodically by the mobile app while the map screen is open."""
    uid = current_user["sub"]
    await _set_location(uid, {
        "lat": loc.latitude,
        "lng": loc.longitude,
        "updated_at": time.time(),
    })
    return {"status": "ok", "ttl_seconds": LOCATION_TTL}


@router.delete("/location")
async def clear_my_location(current_user: dict = Depends(get_current_user)):
    """Called when the user leaves the map / signs out."""
    await _delete_location(current_user["sub"])
    return {"status": "cleared"}


@router.get("/nearby", response_model=List[NearbyUser])
async def get_nearby(current_user: dict = Depends(get_current_user)):
    """Return all users currently live on the map (self + everyone with fresh pings)."""
    me_id = current_user["sub"]
    now = time.time()

    locations = await _get_all_locations()
    if not locations:
        return []

    db = get_databases()
    out: List[NearbyUser] = []
    for uid, v in locations.items():
        try:
            user = db.get_document(
                database_id=APPWRITE_DATABASE_ID,
                collection_id=COLLECTION_USERS,
                document_id=uid,
            )
            out.append(NearbyUser(
                user_id=uid,
                username=user.get("username", ""),
                display_name=user.get("display_name", user.get("username", "User")),
                avatar_url=user.get("avatar_url", ""),
                latitude=v["lat"],
                longitude=v["lng"],
                seconds_ago=int(now - v["updated_at"]),
                is_me=(uid == me_id),
            ))
        except Exception as e:
            logger.warning(f"map: skipping user {uid}: {e}")
            continue

    return out


@router.get("/trending")
@cached(ttl=60, key_fn=lambda current_user: "trending:global")
async def trending(current_user: dict = Depends(get_current_user)):
    """Global live-map data: every active user pinned with their top domain,
    plus the 24-hour trending domains across the platform."""
    db = get_databases()

    # ── Live users ──
    now = time.time()
    locations = await _get_all_locations()

    live_users = []
    for uid, v in locations.items():
        try:
            user = db.get_document(
                database_id=APPWRITE_DATABASE_ID,
                collection_id=COLLECTION_USERS,
                document_id=uid,
            )
            try:
                tags = json.loads(user.get("interest_tags") or "[]")
            except Exception:
                tags = []
            top_domain = next((t for t in tags if t in KNOWN_DOMAINS), tags[0] if tags else None)
            live_users.append({
                "user_id": uid,
                "username": user.get("username", ""),
                "display_name": user.get("display_name", user.get("username", "User")),
                "latitude": v["lat"],
                "longitude": v["lng"],
                "top_domain": top_domain,
                "seconds_ago": int(now - v["updated_at"]),
            })
        except Exception:
            continue

    # ── 24-hour trending domains ──
    domain_count: dict = defaultdict(int)
    cutoff = (datetime.utcnow() - timedelta(hours=24)).strftime("%Y-%m-%dT%H:%M:%S.000+00:00")
    try:
        ir = db.list_documents(
            database_id=APPWRITE_DATABASE_ID,
            collection_id=COLLECTION_INTERACTIONS,
            queries=[Query.greater_than("$createdAt", cutoff), Query.limit(2000)],
        )
        interactions = ir.get("documents", []) or []
    except Exception as e:
        logger.warning(f"trending: interactions fetch failed: {e}")
        interactions = []

    real_cids = list({
        i.get("content_id") for i in interactions
        if i.get("content_id") and i["content_id"] not in KNOWN_DOMAINS
    })
    content_domain: dict = {}
    for start in range(0, len(real_cids), 100):
        chunk = real_cids[start:start + 100]
        try:
            cr = db.list_documents(
                database_id=APPWRITE_DATABASE_ID,
                collection_id=COLLECTION_CONTENT,
                queries=[Query.equal("$id", chunk), Query.limit(100)],
            )
            for doc in cr.get("documents", []):
                content_domain[doc["$id"]] = doc.get("domain")
        except Exception:
            continue

    for ia in interactions:
        cid = ia.get("content_id")
        if cid in KNOWN_DOMAINS:
            domain = cid
        else:
            domain = content_domain.get(cid)
        if domain:
            domain_count[domain] += 1

    sorted_domains = sorted(domain_count.items(), key=lambda kv: kv[1], reverse=True)[:10]

    return {
        "live_users": live_users,
        "active_count": len(live_users),
        "trending_domains": [
            {"domain": d, "count": c} for d, c in sorted_domains
        ],
        "total_interactions_24h": sum(domain_count.values()),
    }
