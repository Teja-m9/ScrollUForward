"""Chat Service — port 8005
Real-time WebSocket chat with rooms, presence tracking, and message persistence.
"""
from __future__ import annotations
import os, sys, json, asyncio
from datetime import datetime, timezone
from typing import Dict, Set, Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Header, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))
from microservices.shared.config import (
    APPWRITE_DATABASE_ID, COLLECTION_MESSAGES, COLLECTION_CHAT_ROOMS, COLLECTION_USERS,
)
from microservices.shared.appwrite_client import get_db
from microservices.shared.redis_client import cache_get, cache_set, cache_delete_pattern
from microservices.shared.auth import decode_token
from appwrite.id import ID
from appwrite.query import Query as AQ

# ── App ────────────────────────────────────────────────────────────────────
app = FastAPI(title="Chat Service", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

# ── Connection Manager ─────────────────────────────────────────────────────
class ConnectionManager:
    """Manages WebSocket connections per chat room."""

    def __init__(self):
        # room_id -> set of (websocket, user_info) tuples
        self.rooms: Dict[str, Dict[str, WebSocket]] = {}
        # websocket_id -> user_info
        self.user_map: Dict[int, dict] = {}

    async def connect(self, ws: WebSocket, room_id: str, user: dict):
        await ws.accept()
        if room_id not in self.rooms:
            self.rooms[room_id] = {}
        self.rooms[room_id][user["user_id"]] = ws
        self.user_map[id(ws)] = user
        await self.broadcast_presence(room_id, user["user_id"], "joined")

    def disconnect(self, ws: WebSocket, room_id: str):
        user = self.user_map.pop(id(ws), None)
        if room_id in self.rooms and user:
            self.rooms[room_id].pop(user["user_id"], None)
            if not self.rooms[room_id]:
                del self.rooms[room_id]
        return user

    async def broadcast(self, room_id: str, message: dict, exclude_user_id: Optional[str] = None):
        if room_id not in self.rooms:
            return
        dead = []
        for uid, ws in list(self.rooms[room_id].items()):
            if uid == exclude_user_id:
                continue
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(uid)
        for uid in dead:
            self.rooms[room_id].pop(uid, None)

    async def send_to_user(self, room_id: str, user_id: str, message: dict):
        ws = self.rooms.get(room_id, {}).get(user_id)
        if ws:
            try:
                await ws.send_json(message)
            except Exception:
                pass

    async def broadcast_presence(self, room_id: str, user_id: str, event: str):
        await self.broadcast(room_id, {
            "type": "presence",
            "event": event,
            "user_id": user_id,
            "online_count": len(self.rooms.get(room_id, {})),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }, exclude_user_id=user_id)

    def get_online_count(self, room_id: str) -> int:
        return len(self.rooms.get(room_id, {}))

    def get_online_users(self, room_id: str) -> list:
        return list(self.rooms.get(room_id, {}).keys())


manager = ConnectionManager()

# ── Auth helper ────────────────────────────────────────────────────────────
async def current_user(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "Missing bearer token")
    payload = decode_token(authorization[7:])
    if not payload:
        raise HTTPException(401, "Invalid token")
    return payload

def verify_ws_token(token: str) -> Optional[dict]:
    return decode_token(token)

# ── Schemas ────────────────────────────────────────────────────────────────
class CreateRoomReq(BaseModel):
    name: str
    description: str = ""
    room_type: str = "public"  # public | private | direct

class SendMessageReq(BaseModel):
    body: str
    message_type: str = "text"  # text | image | system
    reply_to: Optional[str] = None

# ── Room management ────────────────────────────────────────────────────────
@app.post("/chat/rooms")
async def create_room(req: CreateRoomReq, user=Depends(current_user)):
    db = get_db()
    now = datetime.now(timezone.utc).isoformat()
    doc = db.create_document(
        APPWRITE_DATABASE_ID, COLLECTION_CHAT_ROOMS, ID.unique(),
        {
            "name": req.name,
            "description": req.description,
            "room_type": req.room_type,
            "created_by": user["user_id"],
            "members": [user["user_id"]],
            "message_count": 0,
            "created_at": now,
            "updated_at": now,
        }
    )
    return doc

@app.get("/chat/rooms")
async def list_rooms(room_type: str = "public", limit: int = Query(20, le=50)):
    cache_key = f"chat_rooms:{room_type}:{limit}"
    cached = await cache_get(cache_key)
    if cached:
        return cached

    db = get_db()
    queries = [AQ.equal("room_type", room_type), AQ.order_desc("updated_at"), AQ.limit(limit)]
    result = db.list_documents(APPWRITE_DATABASE_ID, COLLECTION_CHAT_ROOMS, queries)

    # Enrich with live online counts
    for doc in result["documents"]:
        doc["online_count"] = manager.get_online_count(doc["$id"])

    await cache_set(cache_key, result, 30)  # short TTL — online counts change fast
    return result

@app.get("/chat/rooms/{room_id}")
async def get_room(room_id: str):
    db = get_db()
    try:
        doc = db.get_document(APPWRITE_DATABASE_ID, COLLECTION_CHAT_ROOMS, room_id)
        doc["online_count"] = manager.get_online_count(room_id)
        doc["online_users"] = manager.get_online_users(room_id)
        return doc
    except Exception:
        raise HTTPException(404, "Room not found")

@app.post("/chat/rooms/{room_id}/join")
async def join_room(room_id: str, user=Depends(current_user)):
    db = get_db()
    try:
        doc = db.get_document(APPWRITE_DATABASE_ID, COLLECTION_CHAT_ROOMS, room_id)
    except Exception:
        raise HTTPException(404, "Room not found")

    members = doc.get("members", [])
    if user["user_id"] not in members:
        members.append(user["user_id"])
        db.update_document(
            APPWRITE_DATABASE_ID, COLLECTION_CHAT_ROOMS, room_id,
            {"members": members, "updated_at": datetime.now(timezone.utc).isoformat()}
        )
    return {"joined": True}

# ── Message history (REST) ─────────────────────────────────────────────────
@app.get("/chat/rooms/{room_id}/messages")
async def get_messages(room_id: str, limit: int = Query(50, le=100), before: Optional[str] = None):
    db = get_db()
    queries = [AQ.equal("room_id", room_id), AQ.order_desc("$createdAt"), AQ.limit(limit)]
    if before:
        queries.append(AQ.less_than("$createdAt", before))

    result = db.list_documents(APPWRITE_DATABASE_ID, COLLECTION_MESSAGES, queries)
    # Return in ascending order for display
    result["documents"] = list(reversed(result["documents"]))
    return result

@app.delete("/chat/rooms/{room_id}/messages/{message_id}")
async def delete_message(room_id: str, message_id: str, user=Depends(current_user)):
    db = get_db()
    try:
        msg = db.get_document(APPWRITE_DATABASE_ID, COLLECTION_MESSAGES, message_id)
    except Exception:
        raise HTTPException(404, "Message not found")

    if msg["sender_id"] != user["user_id"]:
        raise HTTPException(403, "Not the sender")

    db.delete_document(APPWRITE_DATABASE_ID, COLLECTION_MESSAGES, message_id)
    # Broadcast deletion to room
    await manager.broadcast(room_id, {
        "type": "message_deleted",
        "message_id": message_id,
        "room_id": room_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })
    return {"deleted": True}

# ── WebSocket ──────────────────────────────────────────────────────────────
@app.websocket("/chat/ws/{room_id}")
async def websocket_endpoint(ws: WebSocket, room_id: str, token: str = ""):
    # Authenticate via query param token
    user = verify_ws_token(token)
    if not user:
        await ws.close(code=4001, reason="Unauthorized")
        return

    await manager.connect(ws, room_id, user)
    db = get_db()

    # Send last 20 messages on connect
    try:
        history = db.list_documents(
            APPWRITE_DATABASE_ID, COLLECTION_MESSAGES,
            [AQ.equal("room_id", room_id), AQ.order_desc("$createdAt"), AQ.limit(20)]
        )
        history["documents"] = list(reversed(history["documents"]))
        await ws.send_json({
            "type": "history",
            "messages": history["documents"],
            "online_count": manager.get_online_count(room_id),
        })
    except Exception as e:
        print(f"[Chat WS] Failed to send history: {e}")

    try:
        while True:
            raw = await ws.receive_text()
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                await ws.send_json({"type": "error", "message": "Invalid JSON"})
                continue

            msg_type = data.get("type", "message")

            if msg_type == "message":
                body = data.get("body", "").strip()
                if not body:
                    continue
                if len(body) > 2000:
                    await ws.send_json({"type": "error", "message": "Message too long"})
                    continue

                now = datetime.now(timezone.utc).isoformat()
                # Persist message
                try:
                    msg_doc = db.create_document(
                        APPWRITE_DATABASE_ID, COLLECTION_MESSAGES, ID.unique(),
                        {
                            "room_id": room_id,
                            "sender_id": user["user_id"],
                            "sender_username": user.get("username", ""),
                            "sender_avatar": user.get("avatar_url", ""),
                            "body": body,
                            "message_type": data.get("message_type", "text"),
                            "reply_to": data.get("reply_to"),
                            "created_at": now,
                        }
                    )
                    # Bump room message count
                    try:
                        room = db.get_document(APPWRITE_DATABASE_ID, COLLECTION_CHAT_ROOMS, room_id)
                        db.update_document(
                            APPWRITE_DATABASE_ID, COLLECTION_CHAT_ROOMS, room_id,
                            {"message_count": room.get("message_count", 0) + 1, "updated_at": now}
                        )
                    except Exception:
                        pass

                    broadcast_payload = {
                        "type": "message",
                        "id": msg_doc["$id"],
                        "room_id": room_id,
                        "sender_id": user["user_id"],
                        "sender_username": user.get("username", ""),
                        "sender_avatar": user.get("avatar_url", ""),
                        "body": body,
                        "message_type": data.get("message_type", "text"),
                        "reply_to": data.get("reply_to"),
                        "timestamp": now,
                    }
                    # Send to all in room (including sender for confirmation)
                    await manager.broadcast(room_id, broadcast_payload)
                    await ws.send_json(broadcast_payload)  # echo to sender

                except Exception as e:
                    await ws.send_json({"type": "error", "message": f"Failed to send: {e}"})

            elif msg_type == "typing":
                await manager.broadcast(room_id, {
                    "type": "typing",
                    "user_id": user["user_id"],
                    "username": user.get("username", ""),
                    "is_typing": data.get("is_typing", True),
                }, exclude_user_id=user["user_id"])

            elif msg_type == "ping":
                await ws.send_json({"type": "pong", "timestamp": datetime.now(timezone.utc).isoformat()})

    except WebSocketDisconnect:
        left_user = manager.disconnect(ws, room_id)
        if left_user:
            await manager.broadcast_presence(room_id, left_user["user_id"], "left")

# ── Direct Message ─────────────────────────────────────────────────────────
COLLECTION_DM = "direct_messages"

def _dm_room_id(user_a: str, user_b: str) -> str:
    """Deterministic DM room ID from two user IDs."""
    return "dm_" + "_".join(sorted([user_a, user_b]))

@app.post("/chat/dm/{recipient_id}")
async def send_dm(recipient_id: str, req: SendMessageReq, user=Depends(current_user)):
    if user["user_id"] == recipient_id:
        raise HTTPException(400, "Cannot DM yourself")

    room_id = _dm_room_id(user["user_id"], recipient_id)
    db = get_db()
    now = datetime.now(timezone.utc).isoformat()

    msg = db.create_document(
        APPWRITE_DATABASE_ID, COLLECTION_DM, ID.unique(),
        {
            "room_id": room_id,
            "sender_id": user["user_id"],
            "recipient_id": recipient_id,
            "body": req.body,
            "message_type": req.message_type,
            "reply_to": req.reply_to,
            "read": False,
            "created_at": now,
        }
    )
    # Push to recipient via WS if online
    await manager.send_to_user(room_id, recipient_id, {
        "type": "dm",
        "id": msg["$id"],
        "from": user["user_id"],
        "from_username": user.get("username", ""),
        "body": req.body,
        "timestamp": now,
    })
    return msg

@app.get("/chat/dm/{recipient_id}")
async def get_dm_history(recipient_id: str, me=Depends(current_user), limit: int = Query(50, le=100)):
    room_id = _dm_room_id(me["user_id"], recipient_id)
    db = get_db()
    result = db.list_documents(
        APPWRITE_DATABASE_ID, COLLECTION_DM,
        [AQ.equal("room_id", room_id), AQ.order_asc("$createdAt"), AQ.limit(limit)]
    )
    return result

@app.post("/chat/dm/{recipient_id}/read")
async def mark_dm_read(recipient_id: str, me=Depends(current_user)):
    room_id = _dm_room_id(me["user_id"], recipient_id)
    db = get_db()
    unread = db.list_documents(
        APPWRITE_DATABASE_ID, COLLECTION_DM,
        [AQ.equal("room_id", room_id), AQ.equal("recipient_id", me["user_id"]), AQ.equal("read", False), AQ.limit(100)]
    )
    for msg in unread["documents"]:
        try:
            db.update_document(APPWRITE_DATABASE_ID, COLLECTION_DM, msg["$id"], {"read": True})
        except Exception:
            pass
    return {"marked_read": unread["total"]}

# ── Presence REST ──────────────────────────────────────────────────────────
@app.get("/chat/rooms/{room_id}/presence")
async def room_presence(room_id: str):
    return {
        "room_id": room_id,
        "online_count": manager.get_online_count(room_id),
        "online_users": manager.get_online_users(room_id),
    }

# ── Health ─────────────────────────────────────────────────────────────────
@app.get("/chat/health")
async def health():
    return {
        "status": "ok",
        "service": "chat",
        "port": 8005,
        "active_rooms": len(manager.rooms),
        "total_connections": sum(len(v) for v in manager.rooms.values()),
    }
