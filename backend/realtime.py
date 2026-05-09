"""
Real-time WebSocket manager — Stage 1 upgrade with Redis pub/sub.

Each FastAPI worker / Railway instance keeps its own dict of active WebSockets
(can't share live socket FDs across processes). When a worker wants to
broadcast, it publishes to a Redis channel that all workers subscribe to.
A per-process subscriber loop receives the published events and fans them
out to whichever sockets that process actually owns.

Falls back to single-process in-memory broadcast when Redis is unavailable.
"""
import asyncio
import json
import logging
from typing import Dict, List, Set

from fastapi import WebSocket, WebSocketDisconnect
from auth import decode_token
from cache import get_redis

logger = logging.getLogger(__name__)


# Redis channels
CHAN_PERSONAL = "ws:user"           # ws:user:{user_id}
CHAN_ROOM = "ws:room"               # ws:room:{room_id}


class ConnectionManager:
    """Per-process socket registry. Cross-process sync happens via Redis pubsub."""

    def __init__(self):
        # user_id -> list of active WebSocket connections (this process only)
        self.active_connections: Dict[str, List[WebSocket]] = {}
        # room_id -> set of user_ids currently in that room (this process only)
        self.room_members: Dict[str, Set[str]] = {}
        self._subscriber_task: asyncio.Task | None = None
        self._sub_lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)
        await self._ensure_subscriber()

    def disconnect(self, websocket: WebSocket, user_id: str):
        if user_id in self.active_connections:
            self.active_connections[user_id] = [
                ws for ws in self.active_connections[user_id] if ws != websocket
            ]
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]

        for room_id in list(self.room_members.keys()):
            self.room_members[room_id].discard(user_id)
            if not self.room_members[room_id]:
                del self.room_members[room_id]

    def join_room(self, user_id: str, room_id: str):
        if room_id not in self.room_members:
            self.room_members[room_id] = set()
        self.room_members[room_id].add(user_id)

    def leave_room(self, user_id: str, room_id: str):
        if room_id in self.room_members:
            self.room_members[room_id].discard(user_id)

    async def _send_to_local(self, user_id: str, message: dict):
        """Fan-out a message to every WebSocket THIS PROCESS owns for `user_id`."""
        if user_id not in self.active_connections:
            return
        dead = []
        for ws in self.active_connections[user_id]:
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            try:
                self.active_connections[user_id].remove(ws)
            except ValueError:
                pass

    # ── Public broadcast API (Redis pubsub when available, in-process otherwise) ──
    async def send_personal(self, user_id: str, message: dict):
        """Send to one user across ALL instances."""
        r = await get_redis()
        if r is not None:
            try:
                await r.publish(f"{CHAN_PERSONAL}:{user_id}", json.dumps(message, default=str))
                return
            except Exception as e:
                logger.warning(f"WS publish failed, falling back to local: {e}")
        await self._send_to_local(user_id, message)

    async def broadcast_to_room(self, room_id: str, message: dict, exclude_user: str | None = None):
        """Broadcast to every user in `room_id`, regardless of which instance they're on."""
        r = await get_redis()
        payload = {"_msg": message, "_exclude": exclude_user}
        if r is not None:
            try:
                await r.publish(f"{CHAN_ROOM}:{room_id}", json.dumps(payload, default=str))
                return
            except Exception as e:
                logger.warning(f"WS room publish failed, falling back to local: {e}")
        # Fallback: this process's room members only
        if room_id in self.room_members:
            for uid in list(self.room_members[room_id]):
                if uid != exclude_user:
                    await self._send_to_local(uid, message)

    async def broadcast_to_users(self, user_ids: list, message: dict, exclude_user: str | None = None):
        for uid in user_ids:
            if uid != exclude_user:
                await self.send_personal(uid, message)

    def get_online_users(self) -> list:
        """Per-process online users only — for cross-instance presence we'd need a Redis SET."""
        return list(self.active_connections.keys())

    # ── Background subscriber loop (started lazily on first connect) ──
    async def _ensure_subscriber(self):
        if self._subscriber_task and not self._subscriber_task.done():
            return
        async with self._sub_lock:
            if self._subscriber_task and not self._subscriber_task.done():
                return
            r = await get_redis()
            if r is None:
                return  # in-memory only mode
            self._subscriber_task = asyncio.create_task(self._subscribe_forever())

    async def _subscribe_forever(self):
        """Listen to ws:user:* and ws:room:* and dispatch to local sockets."""
        r = await get_redis()
        if r is None:
            return
        try:
            pubsub = r.pubsub(ignore_subscribe_messages=True)
            await pubsub.psubscribe(f"{CHAN_PERSONAL}:*", f"{CHAN_ROOM}:*")
            logger.info("WS pub/sub subscriber started")
            async for raw in pubsub.listen():
                if raw is None:
                    continue
                try:
                    channel = raw.get("channel") or ""
                    data = raw.get("data") or "{}"
                    payload = json.loads(data)
                except Exception:
                    continue

                if channel.startswith(f"{CHAN_PERSONAL}:"):
                    uid = channel.split(":", 2)[-1]
                    if uid in self.active_connections:
                        await self._send_to_local(uid, payload)

                elif channel.startswith(f"{CHAN_ROOM}:"):
                    room_id = channel.split(":", 2)[-1]
                    msg = payload.get("_msg", {})
                    exclude = payload.get("_exclude")
                    members = self.room_members.get(room_id, set())
                    for uid in list(members):
                        if uid != exclude:
                            await self._send_to_local(uid, msg)
        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.warning(f"WS subscriber crashed: {e}; will respawn on next connect")
            self._subscriber_task = None


manager = ConnectionManager()


async def websocket_endpoint(websocket: WebSocket, token: str):
    """Main WebSocket handler for real-time communication."""
    try:
        payload = decode_token(token)
        user_id = payload["sub"]
        username = payload.get("username", "")
    except Exception:
        await websocket.close(code=4001, reason="Invalid token")
        return

    await manager.connect(websocket, user_id)

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            msg_type = message.get("type", "")

            if msg_type == "join_room":
                room_id = message.get("room_id", "")
                manager.join_room(user_id, room_id)
                await manager.broadcast_to_room(room_id, {
                    "type": "user_joined",
                    "user_id": user_id,
                    "username": username,
                    "room_id": room_id,
                }, exclude_user=user_id)

            elif msg_type == "leave_room":
                room_id = message.get("room_id", "")
                manager.leave_room(user_id, room_id)
                await manager.broadcast_to_room(room_id, {
                    "type": "user_left",
                    "user_id": user_id,
                    "username": username,
                    "room_id": room_id,
                })

            elif msg_type == "chat_message":
                room_id = message.get("room_id", "")
                body = message.get("body", "")
                await manager.broadcast_to_room(room_id, {
                    "type": "chat_message",
                    "room_id": room_id,
                    "sender_id": user_id,
                    "sender_username": username,
                    "body": body,
                    "message_type": message.get("message_type", "text"),
                })

            elif msg_type == "typing":
                room_id = message.get("room_id", "")
                await manager.broadcast_to_room(room_id, {
                    "type": "typing",
                    "user_id": user_id,
                    "username": username,
                    "room_id": room_id,
                }, exclude_user=user_id)

            elif msg_type == "ping":
                await manager.send_personal(user_id, {"type": "pong"})

    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
    except Exception:
        manager.disconnect(websocket, user_id)
