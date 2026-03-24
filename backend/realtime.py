"""
Real-time WebSocket manager for ScrollUForward.
Handles live chat messaging and notifications.
"""
import json
from typing import Dict, List, Set
from fastapi import WebSocket, WebSocketDisconnect
from auth import decode_token


class ConnectionManager:
    """Manages WebSocket connections for real-time features."""

    def __init__(self):
        # user_id -> list of active WebSocket connections
        self.active_connections: Dict[str, List[WebSocket]] = {}
        # chat_room_id -> set of user_ids currently in that room
        self.room_members: Dict[str, Set[str]] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)

    def disconnect(self, websocket: WebSocket, user_id: str):
        if user_id in self.active_connections:
            self.active_connections[user_id] = [
                ws for ws in self.active_connections[user_id] if ws != websocket
            ]
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]

        # Remove from all rooms
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

    async def send_personal(self, user_id: str, message: dict):
        if user_id in self.active_connections:
            for ws in self.active_connections[user_id]:
                try:
                    await ws.send_json(message)
                except Exception:
                    pass

    async def broadcast_to_room(self, room_id: str, message: dict, exclude_user: str = None):
        if room_id in self.room_members:
            for uid in self.room_members[room_id]:
                if uid != exclude_user:
                    await self.send_personal(uid, message)

    async def broadcast_to_users(self, user_ids: list, message: dict, exclude_user: str = None):
        for uid in user_ids:
            if uid != exclude_user:
                await self.send_personal(uid, message)

    def get_online_users(self) -> list:
        return list(self.active_connections.keys())


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
