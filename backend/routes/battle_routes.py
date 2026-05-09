"""
Knowledge Battle — 1v1 live quiz duels.

Flow:
  POST /battle/queue        → join domain queue; returns battle_id when matched
  GET  /battle/{id}/state   → poll for state (both players use this — ~1s)
  POST /battle/{id}/answer  → submit answer (question_idx + answer_idx + time_ms)
  POST /battle/{id}/leave   → forfeit
  GET  /battle/leaderboard  → top duelists by rating

In-memory state keeps this simple (no Appwrite schema changes). Fine for MVP;
swap to Redis or Appwrite docs later if we need multi-worker correctness.
"""
import asyncio
import logging
import random
import string
import time
import uuid
import json
import re
from collections import defaultdict, deque
from fastapi import APIRouter, HTTPException, Depends, Query as QueryParam, Request
from pydantic import BaseModel, Field
from typing import List, Optional
from groq import Groq

from auth import get_current_user
from appwrite_client import get_databases
from rate_limit import limiter
from config import (
    APPWRITE_DATABASE_ID, COLLECTION_USERS,
    GROQ_API_KEY, GROQ_MODEL_PRIMARY,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/battle", tags=["Battle"])

# ── Tunables ──────────────────────────────────────────────
QUESTION_COUNT = 5
QUESTION_TIME_S = 10
MATCHMAKE_TIMEOUT_S = 30          # how long a queue join will wait
ELO_K = 24
BASE_POINTS = 100
SPEED_BONUS_FAST = 50   # <=3s
SPEED_BONUS_MID = 25    # <=6s
KNOWN_DOMAINS = {
    "physics", "ai", "space", "biology", "history",
    "technology", "nature", "mathematics", "chemistry",
    "philosophy", "engineering", "ancient_civilizations",
}

# ── In-memory stores (process-local) ──────────────────────
_queues: dict = defaultdict(deque)            # domain -> deque[(user_id, join_ts)]  (solo)
_team_queues: dict = defaultdict(deque)       # (domain, size) -> deque[(team_id, joined_at)]
_battles: dict = {}                           # battle_id -> battle dict
_user_active: dict = {}                       # user_id -> battle_id
_team_active: dict = {}                       # team_id -> battle_id
_ratings: dict = {}                           # user_id -> {rating, wins, losses, username}
_queue_lock = asyncio.Lock()
_team_queue_lock = asyncio.Lock()

# Team store
_teams: dict = {}                             # team_id -> team dict
_user_teams: dict = defaultdict(set)          # user_id -> set[team_id]
_team_codes: dict = {}                        # 6-char invite code -> team_id

MAX_TEAM_SIZE = 4


# ── Helpers ───────────────────────────────────────────────
def _get_rating(uid: str, username: str = "") -> dict:
    if uid not in _ratings:
        _ratings[uid] = {"rating": 1000, "wins": 0, "losses": 0, "draws": 0,
                          "username": username or uid[:8]}
    elif username and not _ratings[uid].get("username"):
        _ratings[uid]["username"] = username
    return _ratings[uid]


def _username_for(uid: str) -> str:
    try:
        db = get_databases()
        doc = db.get_document(
            database_id=APPWRITE_DATABASE_ID,
            collection_id=COLLECTION_USERS,
            document_id=uid,
        )
        return doc.get("display_name") or doc.get("username") or uid[:8]
    except Exception:
        return uid[:8]


async def _generate_questions(domain: str) -> List[dict]:
    """Stage 4: serve from Redis pool when available; fall back to inline Groq."""

    # Try pool first
    try:
        import json as _json
        import random as _random
        from cache import get_redis
        r = await get_redis()
        if r is not None:
            pool = await r.lrange(f"quiz:pool:{domain}", 0, -1)
            if pool and len(pool) >= QUESTION_COUNT:
                sample = _random.sample(pool, QUESTION_COUNT)
                parsed = []
                for raw in sample:
                    try:
                        q = _json.loads(raw)
                        parsed.append({
                            "q": q["q"],
                            "options": q["options"],
                            "correct": q["correct"],
                            "explanation": q.get("explanation", ""),
                        })
                    except Exception:
                        continue
                if len(parsed) >= QUESTION_COUNT:
                    return parsed
    except Exception as e:
        logger.warning(f"battle: pool read failed, falling back to Groq: {e}")

    prompt = f"""Generate exactly {QUESTION_COUNT} multiple-choice quiz questions about {domain}.
REQUIREMENTS:
- Each question has exactly 4 options
- Mix difficulties (easy/medium/hard)
- Vary the correct answer position (don't always B or C)
- Add a 1-sentence explanation
Return ONLY valid JSON:
{{"questions":[{{"q":"...","options":["a","b","c","d"],"correct":0,"explanation":"..."}}]}}"""

    def _call():
        g = Groq(api_key=GROQ_API_KEY)
        resp = g.chat.completions.create(
            model=GROQ_MODEL_PRIMARY,
            messages=[
                {"role": "system", "content": "You are a strict JSON-only quiz generator."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=1800,
            temperature=0.85,
        )
        return resp.choices[0].message.content.strip()

    try:
        raw = await asyncio.to_thread(_call)
        cleaned = raw
        if "```" in cleaned:
            cleaned = cleaned.split("```")[1]
            if cleaned.startswith("json"):
                cleaned = cleaned[4:]
            cleaned = cleaned.strip()
        data = json.loads(cleaned)
        out = []
        for q in data.get("questions", [])[:QUESTION_COUNT]:
            if (isinstance(q.get("q"), str)
                    and isinstance(q.get("options"), list) and len(q["options"]) == 4
                    and isinstance(q.get("correct"), int) and 0 <= q["correct"] <= 3):
                out.append({
                    "q": q["q"],
                    "options": q["options"],
                    "correct": q["correct"],
                    "explanation": q.get("explanation", ""),
                })
        if len(out) >= 3:
            return out
    except Exception as e:
        logger.warning(f"battle: Groq gen failed: {e}")

    # Minimal fallback (rare — Groq is usually fine)
    return [
        {"q": f"Sample {domain} question {i+1}?",
         "options": ["Option A", "Option B", "Option C", "Option D"],
         "correct": i % 4, "explanation": ""}
        for i in range(QUESTION_COUNT)
    ]


def _make_battle(p1_id: str, p2_id: str, domain: str, questions: list) -> dict:
    bid = uuid.uuid4().hex[:12]
    now = time.time()
    battle = {
        "id": bid,
        "domain": domain,
        "status": "active",       # active | finished | cancelled
        "p1": {
            "user_id": p1_id,
            "username": _username_for(p1_id),
            "score": 0, "correct": 0,
            "rating_before": _get_rating(p1_id).get("rating", 1000),
        },
        "p2": {
            "user_id": p2_id,
            "username": _username_for(p2_id),
            "score": 0, "correct": 0,
            "rating_before": _get_rating(p2_id).get("rating", 1000),
        },
        "questions": questions,
        "current_idx": 0,
        "question_started_at": now,
        "answers": {},            # key: f"{uid}:{idx}" → {answer_idx, time_ms, is_correct, points}
        "winner_id": None,
        "rating_deltas": {p1_id: 0, p2_id: 0},
        "created_at": now,
    }
    _battles[bid] = battle
    _user_active[p1_id] = bid
    _user_active[p2_id] = bid
    return battle


def _advance_if_ready(battle: dict):
    """Move to the next question when both answered OR timer expired."""
    if battle["status"] != "active":
        return
    idx = battle["current_idx"]
    p1_id = battle["p1"]["user_id"]
    p2_id = battle["p2"]["user_id"]
    p1_done = f"{p1_id}:{idx}" in battle["answers"]
    p2_done = f"{p2_id}:{idx}" in battle["answers"]
    elapsed = time.time() - battle["question_started_at"]

    if (p1_done and p2_done) or elapsed >= QUESTION_TIME_S:
        # Force 0-point timeouts for players who didn't answer
        for pid in (p1_id, p2_id):
            k = f"{pid}:{idx}"
            if k not in battle["answers"]:
                battle["answers"][k] = {"answer_idx": -1, "time_ms": QUESTION_TIME_S * 1000,
                                         "is_correct": False, "points": 0}

        if idx + 1 >= len(battle["questions"]):
            _finish_battle(battle)
        else:
            battle["current_idx"] = idx + 1
            battle["question_started_at"] = time.time()


def _finish_battle(battle: dict):
    battle["status"] = "finished"
    p1, p2 = battle["p1"], battle["p2"]
    winner_id = None
    if p1["score"] > p2["score"]:
        winner_id = p1["user_id"]
        result_p1 = 1.0
    elif p2["score"] > p1["score"]:
        winner_id = p2["user_id"]
        result_p1 = 0.0
    else:
        result_p1 = 0.5
    battle["winner_id"] = winner_id

    # ELO update
    r1 = _get_rating(p1["user_id"], p1["username"])
    r2 = _get_rating(p2["user_id"], p2["username"])
    e1 = 1 / (1 + 10 ** ((r2["rating"] - r1["rating"]) / 400))
    delta1 = round(ELO_K * (result_p1 - e1))
    delta2 = -delta1
    r1["rating"] += delta1
    r2["rating"] += delta2
    battle["rating_deltas"] = {p1["user_id"]: delta1, p2["user_id"]: delta2}

    if winner_id == p1["user_id"]:
        r1["wins"] += 1; r2["losses"] += 1
    elif winner_id == p2["user_id"]:
        r2["wins"] += 1; r1["losses"] += 1
    else:
        r1["draws"] = r1.get("draws", 0) + 1
        r2["draws"] = r2.get("draws", 0) + 1

    # Release user→battle binding so they can queue again
    _user_active.pop(p1["user_id"], None)
    _user_active.pop(p2["user_id"], None)


def _redact_questions(questions: list, current_idx: int, status: str):
    """Don't leak future questions OR the correct answer while active."""
    out = []
    for i, q in enumerate(questions):
        if status == "active" and i > current_idx:
            out.append(None)
            continue
        out.append({
            "q": q["q"],
            "options": q["options"],
            "correct": q["correct"] if status == "finished" or i < current_idx else None,
            "explanation": q.get("explanation", "") if status == "finished" or i < current_idx else "",
        })
    return out


def _public_state(battle: dict, viewer_id: str) -> dict:
    _advance_if_ready(battle)
    idx = battle["current_idx"]
    elapsed = time.time() - battle["question_started_at"]
    seconds_left = max(0, QUESTION_TIME_S - int(elapsed))
    me_key = "p1" if battle["p1"]["user_id"] == viewer_id else "p2"
    opp_key = "p2" if me_key == "p1" else "p1"
    me_answered = f"{viewer_id}:{idx}" in battle["answers"]
    opp_answered = f"{battle[opp_key]['user_id']}:{idx}" in battle["answers"]

    return {
        "id": battle["id"],
        "status": battle["status"],
        "domain": battle["domain"],
        "me": battle[me_key],
        "opponent": battle[opp_key],
        "current_idx": idx,
        "question_count": len(battle["questions"]),
        "seconds_left": seconds_left,
        "me_answered": me_answered,
        "opp_answered": opp_answered,
        "question": battle["questions"][idx] if battle["status"] == "active" and idx < len(battle["questions"]) else None,
        "winner_id": battle["winner_id"],
        "rating_deltas": battle.get("rating_deltas", {}),
        "questions": _redact_questions(battle["questions"], idx, battle["status"]) if battle["status"] == "finished" else None,
    }


# ── API ───────────────────────────────────────────────────
class QueueRequest(BaseModel):
    domain: str


class AnswerRequest(BaseModel):
    question_idx: int
    answer_idx: int
    time_ms: int


@router.post("/queue")
@limiter.limit("20/hour")
async def join_queue(request: Request, body: QueueRequest, current_user: dict = Depends(get_current_user)):
    uid = current_user["sub"]
    domain = body.domain
    if domain not in KNOWN_DOMAINS:
        raise HTTPException(status_code=400, detail=f"Unknown domain: {domain}")

    # Already in an active battle? Return it.
    if uid in _user_active:
        bid = _user_active[uid]
        if bid in _battles:
            return {"matched": True, "battle_id": bid}
        else:
            _user_active.pop(uid, None)

    async with _queue_lock:
        q = _queues[domain]
        # Is there a waiting opponent? Pair them.
        while q:
            other_id, joined_at = q[0]
            if other_id == uid:
                q.popleft()
                continue
            if other_id in _user_active:
                q.popleft()  # stale
                continue
            # Match!
            q.popleft()
            break
        else:
            other_id = None

    if other_id:
        questions = await _generate_questions(domain)
        battle = _make_battle(other_id, uid, domain, questions)
        return {"matched": True, "battle_id": battle["id"]}

    # No opponent yet — enqueue & long-poll for up to MATCHMAKE_TIMEOUT_S
    async with _queue_lock:
        _queues[domain].append((uid, time.time()))

    deadline = time.time() + MATCHMAKE_TIMEOUT_S
    while time.time() < deadline:
        await asyncio.sleep(0.6)
        if uid in _user_active:
            return {"matched": True, "battle_id": _user_active[uid]}

    # Timeout — leave the queue
    async with _queue_lock:
        _queues[domain] = deque([e for e in _queues[domain] if e[0] != uid])
    return {"matched": False, "reason": "no_opponent_in_time"}


@router.post("/queue/cancel")
async def cancel_queue(body: QueueRequest, current_user: dict = Depends(get_current_user)):
    uid = current_user["sub"]
    async with _queue_lock:
        _queues[body.domain] = deque([e for e in _queues[body.domain] if e[0] != uid])
    return {"status": "cancelled"}


@router.get("/{battle_id}/state")
async def get_state(battle_id: str, current_user: dict = Depends(get_current_user)):
    battle = _battles.get(battle_id)
    if not battle:
        raise HTTPException(status_code=404, detail="Battle not found")
    uid = current_user["sub"]
    if uid not in (battle["p1"]["user_id"], battle["p2"]["user_id"]):
        raise HTTPException(status_code=403, detail="Not a participant")
    return _public_state(battle, uid)


@router.post("/{battle_id}/answer")
async def submit_answer(
    battle_id: str,
    body: AnswerRequest,
    current_user: dict = Depends(get_current_user),
):
    battle = _battles.get(battle_id)
    if not battle:
        raise HTTPException(status_code=404, detail="Battle not found")
    uid = current_user["sub"]
    if uid not in (battle["p1"]["user_id"], battle["p2"]["user_id"]):
        raise HTTPException(status_code=403, detail="Not a participant")
    if battle["status"] != "active":
        raise HTTPException(status_code=400, detail="Battle not active")

    idx = battle["current_idx"]
    if body.question_idx != idx:
        raise HTTPException(status_code=400, detail="Stale question index")

    key = f"{uid}:{idx}"
    if key in battle["answers"]:
        return _public_state(battle, uid)   # idempotent

    q = battle["questions"][idx]
    is_correct = body.answer_idx == q["correct"]
    pts = 0
    if is_correct:
        pts = BASE_POINTS
        if body.time_ms <= 3000:   pts += SPEED_BONUS_FAST
        elif body.time_ms <= 6000: pts += SPEED_BONUS_MID

    battle["answers"][key] = {
        "answer_idx": body.answer_idx,
        "time_ms": body.time_ms,
        "is_correct": is_correct,
        "points": pts,
    }

    # Update side scores
    side = "p1" if battle["p1"]["user_id"] == uid else "p2"
    battle[side]["score"] += pts
    if is_correct:
        battle[side]["correct"] += 1

    _advance_if_ready(battle)
    return _public_state(battle, uid)


@router.post("/{battle_id}/leave")
async def leave_battle(battle_id: str, current_user: dict = Depends(get_current_user)):
    battle = _battles.get(battle_id)
    if not battle:
        return {"status": "gone"}
    uid = current_user["sub"]
    if uid not in (battle["p1"]["user_id"], battle["p2"]["user_id"]):
        raise HTTPException(status_code=403, detail="Not a participant")
    # Forfeit → opponent wins
    if battle["status"] == "active":
        side = "p1" if battle["p1"]["user_id"] == uid else "p2"
        opp = "p2" if side == "p1" else "p1"
        battle[opp]["score"] = max(battle[opp]["score"], battle[side]["score"] + 1)
        _finish_battle(battle)
    return _public_state(battle, uid)


@router.get("/leaderboard")
async def leaderboard(limit: int = QueryParam(20, ge=1, le=100)):
    items = sorted(_ratings.items(), key=lambda kv: kv[1]["rating"], reverse=True)[:limit]
    out = []
    for i, (uid, r) in enumerate(items, 1):
        out.append({
            "rank": i,
            "user_id": uid,
            "username": r.get("username") or uid[:8],
            "rating": r["rating"],
            "wins": r["wins"],
            "losses": r["losses"],
            "draws": r.get("draws", 0),
        })
    return {"count": len(out), "items": out}


# ═══════════════════════════════════════════════════════════
# TEAMS
# ═══════════════════════════════════════════════════════════
def _new_invite_code() -> str:
    while True:
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        if code not in _team_codes:
            return code


def _public_team(team: dict) -> dict:
    return {
        "id": team["id"],
        "name": team["name"],
        "owner_id": team["owner_id"],
        "code": team["code"],
        "created_at": team["created_at"],
        "members": [{
            "user_id": uid,
            "username": _get_rating(uid).get("username") or _username_for(uid),
        } for uid in team["members"]],
        "size": len(team["members"]),
        "active_battle_id": _team_active.get(team["id"]),
    }


class TeamCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=40)


class TeamJoin(BaseModel):
    code: str = Field(..., min_length=4, max_length=12)


class TeamQueueRequest(BaseModel):
    team_id: str
    domain: str


@router.post("/team")
async def create_team(body: TeamCreate, current_user: dict = Depends(get_current_user)):
    uid = current_user["sub"]
    tid = uuid.uuid4().hex[:12]
    code = _new_invite_code()
    username = _username_for(uid)
    _get_rating(uid, username)  # seed username
    team = {
        "id": tid,
        "name": body.name.strip()[:40] or "Untitled Team",
        "owner_id": uid,
        "members": [uid],
        "code": code,
        "created_at": time.time(),
    }
    _teams[tid] = team
    _team_codes[code] = tid
    _user_teams[uid].add(tid)
    return _public_team(team)


@router.post("/team/join")
async def join_team(body: TeamJoin, current_user: dict = Depends(get_current_user)):
    uid = current_user["sub"]
    code = body.code.strip().upper()
    tid = _team_codes.get(code)
    if not tid or tid not in _teams:
        raise HTTPException(status_code=404, detail="Invite code not found")
    team = _teams[tid]
    if uid in team["members"]:
        return _public_team(team)
    if len(team["members"]) >= MAX_TEAM_SIZE:
        raise HTTPException(status_code=400, detail=f"Team is full (max {MAX_TEAM_SIZE})")
    team["members"].append(uid)
    _user_teams[uid].add(tid)
    _get_rating(uid, _username_for(uid))
    return _public_team(team)


@router.post("/team/{team_id}/leave")
async def leave_team(team_id: str, current_user: dict = Depends(get_current_user)):
    uid = current_user["sub"]
    team = _teams.get(team_id)
    if not team:
        return {"status": "gone"}
    if uid not in team["members"]:
        raise HTTPException(status_code=403, detail="Not a member")
    team["members"] = [m for m in team["members"] if m != uid]
    _user_teams[uid].discard(team_id)
    # If the owner leaves, hand ownership to the next member; if empty, disband.
    if not team["members"]:
        _team_codes.pop(team["code"], None)
        _teams.pop(team_id, None)
        _team_active.pop(team_id, None)
        return {"status": "disbanded"}
    if team["owner_id"] == uid:
        team["owner_id"] = team["members"][0]
    return _public_team(team)


@router.delete("/team/{team_id}/members/{member_id}")
async def kick_member(team_id: str, member_id: str, current_user: dict = Depends(get_current_user)):
    uid = current_user["sub"]
    team = _teams.get(team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    if team["owner_id"] != uid:
        raise HTTPException(status_code=403, detail="Only the captain can kick")
    if member_id == uid:
        raise HTTPException(status_code=400, detail="Captain can't kick themselves — leave instead")
    if member_id not in team["members"]:
        raise HTTPException(status_code=404, detail="Member not in team")
    team["members"] = [m for m in team["members"] if m != member_id]
    _user_teams[member_id].discard(team_id)
    return _public_team(team)


@router.get("/team/my")
async def my_teams(current_user: dict = Depends(get_current_user)):
    uid = current_user["sub"]
    out = []
    for tid in list(_user_teams[uid]):
        team = _teams.get(tid)
        if team and uid in team["members"]:
            out.append(_public_team(team))
    return {"count": len(out), "items": out}


@router.get("/team/{team_id}")
async def get_team(team_id: str, current_user: dict = Depends(get_current_user)):
    team = _teams.get(team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    if current_user["sub"] not in team["members"]:
        raise HTTPException(status_code=403, detail="Not a member")
    return _public_team(team)


# ═══════════════════════════════════════════════════════════
# TEAM BATTLE (captain-driven queue)
# ═══════════════════════════════════════════════════════════
def _make_team_battle(team1_id: str, team2_id: str, domain: str, questions: list) -> dict:
    bid = uuid.uuid4().hex[:12]
    now = time.time()
    t1 = _teams[team1_id]
    t2 = _teams[team2_id]

    def member_entry(uid):
        r = _get_rating(uid, _username_for(uid))
        return {
            "user_id": uid,
            "username": r.get("username") or uid[:8],
            "score": 0,
            "correct": 0,
            "rating_before": r.get("rating", 1000),
        }

    battle = {
        "id": bid,
        "mode": "team",
        "domain": domain,
        "status": "active",
        "team1": {
            "team_id": team1_id,
            "name": t1["name"],
            "members": [member_entry(uid) for uid in t1["members"]],
            "score": 0,
            "correct": 0,
        },
        "team2": {
            "team_id": team2_id,
            "name": t2["name"],
            "members": [member_entry(uid) for uid in t2["members"]],
            "score": 0,
            "correct": 0,
        },
        "questions": questions,
        "current_idx": 0,
        "question_started_at": now,
        "answers": {},  # f"{uid}:{idx}" -> {answer_idx, time_ms, is_correct, points}
        "winner_team_id": None,
        "rating_deltas": {},
        "created_at": now,
    }
    _battles[bid] = battle
    _team_active[team1_id] = bid
    _team_active[team2_id] = bid
    for uid in t1["members"] + t2["members"]:
        _user_active[uid] = bid
    return battle


def _advance_team_if_ready(battle: dict):
    if battle["status"] != "active":
        return
    idx = battle["current_idx"]
    all_uids = [m["user_id"] for m in battle["team1"]["members"]] + \
               [m["user_id"] for m in battle["team2"]["members"]]
    all_done = all(f"{uid}:{idx}" in battle["answers"] for uid in all_uids)
    elapsed = time.time() - battle["question_started_at"]

    if all_done or elapsed >= QUESTION_TIME_S:
        for uid in all_uids:
            k = f"{uid}:{idx}"
            if k not in battle["answers"]:
                battle["answers"][k] = {"answer_idx": -1, "time_ms": QUESTION_TIME_S * 1000,
                                         "is_correct": False, "points": 0}

        if idx + 1 >= len(battle["questions"]):
            _finish_team_battle(battle)
        else:
            battle["current_idx"] = idx + 1
            battle["question_started_at"] = time.time()


def _finish_team_battle(battle: dict):
    battle["status"] = "finished"
    t1 = battle["team1"]; t2 = battle["team2"]
    winner_team = None
    if t1["score"] > t2["score"]:
        winner_team = t1["team_id"]
        result1 = 1.0
    elif t2["score"] > t1["score"]:
        winner_team = t2["team_id"]
        result1 = 0.0
    else:
        result1 = 0.5
    battle["winner_team_id"] = winner_team

    # Team average ratings for ELO
    def avg(team):
        vals = [_get_rating(m["user_id"]).get("rating", 1000) for m in team["members"]]
        return sum(vals) / len(vals) if vals else 1000

    r1 = avg(t1); r2 = avg(t2)
    e1 = 1 / (1 + 10 ** ((r2 - r1) / 400))
    delta1 = round(ELO_K * (result1 - e1))
    delta2 = -delta1

    deltas = {}
    for m in t1["members"]:
        r = _get_rating(m["user_id"], m["username"])
        r["rating"] += delta1
        deltas[m["user_id"]] = delta1
        if winner_team == t1["team_id"]: r["wins"] += 1
        elif winner_team == t2["team_id"]: r["losses"] += 1
        else: r["draws"] = r.get("draws", 0) + 1
    for m in t2["members"]:
        r = _get_rating(m["user_id"], m["username"])
        r["rating"] += delta2
        deltas[m["user_id"]] = delta2
        if winner_team == t2["team_id"]: r["wins"] += 1
        elif winner_team == t1["team_id"]: r["losses"] += 1
        else: r["draws"] = r.get("draws", 0) + 1

    battle["rating_deltas"] = deltas

    # Release bindings
    _team_active.pop(t1["team_id"], None)
    _team_active.pop(t2["team_id"], None)
    for m in t1["members"] + t2["members"]:
        _user_active.pop(m["user_id"], None)


def _public_team_state(battle: dict, viewer_id: str) -> dict:
    _advance_team_if_ready(battle)
    idx = battle["current_idx"]
    elapsed = time.time() - battle["question_started_at"]
    seconds_left = max(0, QUESTION_TIME_S - int(elapsed))

    def team_on_side(side_key):
        side = battle[side_key]
        return {
            "team_id": side["team_id"],
            "name": side["name"],
            "score": side["score"],
            "correct": side["correct"],
            "members": side["members"],
            "all_answered": all(
                f"{m['user_id']}:{idx}" in battle["answers"] for m in side["members"]
            ),
            "answered_count": sum(
                1 for m in side["members"] if f"{m['user_id']}:{idx}" in battle["answers"]
            ),
        }

    my_side_key = None
    for key in ("team1", "team2"):
        if any(m["user_id"] == viewer_id for m in battle[key]["members"]):
            my_side_key = key
            break

    if not my_side_key:
        raise HTTPException(status_code=403, detail="Not a participant")
    opp_key = "team2" if my_side_key == "team1" else "team1"
    me_answered = f"{viewer_id}:{idx}" in battle["answers"]

    return {
        "id": battle["id"],
        "mode": "team",
        "status": battle["status"],
        "domain": battle["domain"],
        "my_team": team_on_side(my_side_key),
        "opponent_team": team_on_side(opp_key),
        "current_idx": idx,
        "question_count": len(battle["questions"]),
        "seconds_left": seconds_left,
        "me_answered": me_answered,
        "question": battle["questions"][idx] if battle["status"] == "active" and idx < len(battle["questions"]) else None,
        "winner_team_id": battle.get("winner_team_id"),
        "rating_deltas": battle.get("rating_deltas", {}),
    }


@router.post("/team/queue")
async def team_queue(body: TeamQueueRequest, current_user: dict = Depends(get_current_user)):
    uid = current_user["sub"]
    if body.domain not in KNOWN_DOMAINS:
        raise HTTPException(status_code=400, detail=f"Unknown domain: {body.domain}")
    team = _teams.get(body.team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    if team["owner_id"] != uid:
        raise HTTPException(status_code=403, detail="Only the captain can queue")
    if team["id"] in _team_active:
        return {"matched": True, "battle_id": _team_active[team["id"]]}

    size = len(team["members"])
    if size == 0:
        raise HTTPException(status_code=400, detail="Team has no members")
    key = (body.domain, size)

    async with _team_queue_lock:
        q = _team_queues[key]
        other_team_id = None
        while q:
            tid2, joined_at = q[0]
            if tid2 == team["id"]:
                q.popleft(); continue
            if tid2 not in _teams or tid2 in _team_active:
                q.popleft(); continue
            q.popleft()
            other_team_id = tid2
            break

    if other_team_id:
        questions = await _generate_questions(body.domain)
        battle = _make_team_battle(other_team_id, team["id"], body.domain, questions)
        return {"matched": True, "battle_id": battle["id"]}

    # Enqueue & long-poll
    async with _team_queue_lock:
        _team_queues[key].append((team["id"], time.time()))

    deadline = time.time() + MATCHMAKE_TIMEOUT_S
    while time.time() < deadline:
        await asyncio.sleep(0.6)
        if team["id"] in _team_active:
            return {"matched": True, "battle_id": _team_active[team["id"]]}

    async with _team_queue_lock:
        _team_queues[key] = deque([e for e in _team_queues[key] if e[0] != team["id"]])
    return {"matched": False, "reason": "no_opponent_team"}


@router.post("/team/queue/cancel")
async def team_queue_cancel(body: TeamQueueRequest, current_user: dict = Depends(get_current_user)):
    team = _teams.get(body.team_id)
    if not team:
        return {"status": "gone"}
    size = len(team["members"])
    async with _team_queue_lock:
        _team_queues[(body.domain, size)] = deque(
            [e for e in _team_queues[(body.domain, size)] if e[0] != team["id"]]
        )
    return {"status": "cancelled"}


# ── Patch the solo state endpoint to also handle team battles ──
# (We can't change the path, so just dispatch from inside get_state.)
_original_get_state = get_state

async def _dispatch_state(battle_id: str, current_user: dict):
    battle = _battles.get(battle_id)
    if not battle:
        raise HTTPException(status_code=404, detail="Battle not found")
    if battle.get("mode") == "team":
        return _public_team_state(battle, current_user["sub"])
    return _public_state(battle, current_user["sub"])


# Re-register the route: FastAPI keeps original; we shadow with same path
# by swapping the endpoint function.
for r in list(router.routes):
    if getattr(r, "path", None) == "/battle/{battle_id}/state":
        r.endpoint = lambda battle_id, current_user=Depends(get_current_user): \
            _dispatch_state(battle_id, current_user)
        break


# Override answer endpoint so it works for both modes
@router.post("/team-answer/{battle_id}")
async def team_answer(
    battle_id: str,
    body: AnswerRequest,
    current_user: dict = Depends(get_current_user),
):
    """Submit an answer inside a team battle."""
    battle = _battles.get(battle_id)
    if not battle:
        raise HTTPException(status_code=404, detail="Battle not found")
    if battle.get("mode") != "team":
        raise HTTPException(status_code=400, detail="Use /answer for solo battles")

    uid = current_user["sub"]
    my_side = None
    for key in ("team1", "team2"):
        if any(m["user_id"] == uid for m in battle[key]["members"]):
            my_side = key; break
    if not my_side:
        raise HTTPException(status_code=403, detail="Not a participant")
    if battle["status"] != "active":
        raise HTTPException(status_code=400, detail="Battle not active")

    idx = battle["current_idx"]
    if body.question_idx != idx:
        raise HTTPException(status_code=400, detail="Stale question index")

    key = f"{uid}:{idx}"
    if key in battle["answers"]:
        return _public_team_state(battle, uid)

    q = battle["questions"][idx]
    is_correct = body.answer_idx == q["correct"]
    pts = 0
    if is_correct:
        pts = BASE_POINTS
        if body.time_ms <= 3000:   pts += SPEED_BONUS_FAST
        elif body.time_ms <= 6000: pts += SPEED_BONUS_MID

    battle["answers"][key] = {
        "answer_idx": body.answer_idx,
        "time_ms": body.time_ms,
        "is_correct": is_correct,
        "points": pts,
    }

    # Update member score inside the side
    for m in battle[my_side]["members"]:
        if m["user_id"] == uid:
            m["score"] += pts
            if is_correct:
                m["correct"] += 1
            break
    battle[my_side]["score"] += pts
    if is_correct:
        battle[my_side]["correct"] += 1

    _advance_team_if_ready(battle)
    return _public_team_state(battle, uid)
