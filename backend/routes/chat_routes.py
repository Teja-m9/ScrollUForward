import base64
import logging
from fastapi import APIRouter, HTTPException, Depends, Query as QueryParam, Request
from pydantic import BaseModel, Field
from appwrite.query import Query
from appwrite.id import ID
from auth import get_current_user
from appwrite_client import get_databases
from schemas import ChatRoomCreate, ChatRoomResponse, MessageCreate, MessageResponse
from config import APPWRITE_DATABASE_ID, COLLECTION_CHAT_ROOMS, COLLECTION_MESSAGES, COLLECTION_USERS
from moderation import moderate_comment
from strike_system import check_user_ban_status, record_violation
from s3_client import upload_chat_attachment
from rate_limit import limiter
import json

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("/rooms", response_model=ChatRoomResponse)
async def create_chat_room(room: ChatRoomCreate, current_user: dict = Depends(get_current_user)):
    db = get_databases()
    doc_id = ID.unique()

    all_participants = list(set([current_user["sub"]] + room.participant_ids))

    try:
        doc = db.create_document(
            database_id=APPWRITE_DATABASE_ID,
            collection_id=COLLECTION_CHAT_ROOMS,
            document_id=doc_id,
            data={
                "participants": json.dumps(all_participants),
                "is_group": room.is_group,
                "name": room.name,
                "last_message": "",
                "last_message_time": "",
                "created_by": current_user["sub"],
            }
        )
        return _doc_to_room(doc)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rooms", response_model=list[ChatRoomResponse])
async def list_chat_rooms(current_user: dict = Depends(get_current_user)):
    db = get_databases()
    try:
        result = db.list_documents(
            database_id=APPWRITE_DATABASE_ID,
            collection_id=COLLECTION_CHAT_ROOMS,
            queries=[Query.order_desc("$createdAt"), Query.limit(50)]
        )
        # Filter rooms where current user is a participant
        rooms = []
        for doc in result["documents"]:
            participants = json.loads(doc.get("participants", "[]"))
            if current_user["sub"] in participants:
                rooms.append(_doc_to_room(doc))
        return rooms
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/messages", response_model=MessageResponse)
@limiter.limit("60/minute")
async def send_message(request: Request, msg: MessageCreate, current_user: dict = Depends(get_current_user)):
    from realtime import manager  # local import to avoid circular at module load
    db = get_databases()
    doc_id = ID.unique()

    # ─── Security Firewall (text only for chat) ────────────
    ban_status = await check_user_ban_status(current_user["sub"])
    if not ban_status["allowed"]:
        raise HTTPException(status_code=403, detail=ban_status["reason"])

    mod_result = await moderate_comment(msg.body)
    if not mod_result["safe"]:
        violation_type = mod_result["violations"][0] if mod_result["violations"] else "policy_violation"
        await record_violation(
            user_id=current_user["sub"], violation_type=violation_type,
            details=mod_result.get("details", {}), content_type="message",
            snippet=msg.body[:200],
        )
        raise HTTPException(status_code=400, detail="Message blocked for policy violation.")

    try:
        # Get sender info
        sender = db.get_document(
            database_id=APPWRITE_DATABASE_ID,
            collection_id=COLLECTION_USERS,
            document_id=current_user["sub"]
        )

        doc = db.create_document(
            database_id=APPWRITE_DATABASE_ID,
            collection_id=COLLECTION_MESSAGES,
            document_id=doc_id,
            data={
                "chat_room_id": msg.chat_room_id,
                "sender_id": current_user["sub"],
                "sender_username": current_user["username"],
                "sender_avatar": sender.get("avatar_url", ""),
                "body": msg.body,
                "message_type": msg.message_type,
                "is_read": False,
            }
        )

        # Update last message on room
        db.update_document(
            database_id=APPWRITE_DATABASE_ID,
            collection_id=COLLECTION_CHAT_ROOMS,
            document_id=msg.chat_room_id,
            data={
                "last_message": msg.body[:100],
                "last_message_time": doc.get("$createdAt", ""),
            }
        )

        # Real-time broadcast to all OTHER participants of the room
        try:
            room_doc = db.get_document(
                database_id=APPWRITE_DATABASE_ID,
                collection_id=COLLECTION_CHAT_ROOMS,
                document_id=msg.chat_room_id,
            )
            participants = json.loads(room_doc.get("participants", "[]"))
            saved = _doc_to_message(doc).model_dump() if hasattr(_doc_to_message(doc), "model_dump") else dict(_doc_to_message(doc))
            payload = {
                "type": "new_message",
                "room_id": msg.chat_room_id,
                "message": saved,
            }
            sender_id = current_user["sub"]
            for pid in participants:
                if pid and pid != sender_id:
                    await manager.send_personal(pid, payload)
        except Exception as broadcast_err:
            # Broadcast failure shouldn't fail the send — message is already saved
            import logging
            logging.getLogger(__name__).warning(f"chat: broadcast failed: {broadcast_err}")

        return _doc_to_message(doc)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/messages/{room_id}", response_model=list[MessageResponse])
async def list_messages(
    room_id: str,
    limit: int = QueryParam(50, ge=1, le=100),
    current_user: dict = Depends(get_current_user)
):
    db = get_databases()
    try:
        result = db.list_documents(
            database_id=APPWRITE_DATABASE_ID,
            collection_id=COLLECTION_MESSAGES,
            queries=[
                Query.equal("chat_room_id", room_id),
                Query.order_asc("$createdAt"),
                Query.limit(limit),
            ]
        )
        return [_doc_to_message(d) for d in result["documents"]]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class ChatUploadRequest(BaseModel):
    base64: str = Field(..., description="Raw base64 (no data: prefix)")
    content_type: str = Field("image/jpeg", description="MIME type")
    ext: str = Field("jpg", description="File extension")


@router.post("/upload")
async def upload_attachment(
    body: ChatUploadRequest,
    current_user: dict = Depends(get_current_user),
):
    """Decode a base64 attachment from a chat client and store it on S3.
    Returns a presigned URL the recipient can fetch and render."""
    try:
        raw = body.base64
        if "," in raw and raw[:30].lower().startswith("data:"):
            raw = raw.split(",", 1)[1]
        file_bytes = base64.b64decode(raw)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid base64: {e}")

    if len(file_bytes) > 25 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Attachment too large (max 25 MB)")

    try:
        url = upload_chat_attachment(
            file_bytes=file_bytes,
            user_id=current_user["sub"],
            ext=(body.ext or "bin").lower().lstrip("."),
            content_type=body.content_type or "application/octet-stream",
        )
        return {"url": url, "size": len(file_bytes)}
    except Exception as e:
        logger.error(f"chat upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {e}")


def _doc_to_room(doc: dict) -> ChatRoomResponse:
    return ChatRoomResponse(
        id=doc["$id"],
        participants=json.loads(doc.get("participants", "[]")),
        is_group=doc.get("is_group", False),
        name=doc.get("name", ""),
        last_message=doc.get("last_message", ""),
        last_message_time=doc.get("last_message_time", ""),
    )


def _doc_to_message(doc: dict) -> MessageResponse:
    return MessageResponse(
        id=doc["$id"],
        chat_room_id=doc.get("chat_room_id", ""),
        sender_id=doc.get("sender_id", ""),
        sender_username=doc.get("sender_username", ""),
        sender_avatar=doc.get("sender_avatar", ""),
        body=doc.get("body", ""),
        message_type=doc.get("message_type", "text"),
        created_at=doc.get("$createdAt", ""),
        is_read=doc.get("is_read", False),
    )
