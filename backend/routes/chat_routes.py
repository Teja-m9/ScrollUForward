from fastapi import APIRouter, HTTPException, Depends, Query as QueryParam
from appwrite.query import Query
from appwrite.id import ID
from auth import get_current_user
from appwrite_client import get_databases
from schemas import ChatRoomCreate, ChatRoomResponse, MessageCreate, MessageResponse
from config import APPWRITE_DATABASE_ID, COLLECTION_CHAT_ROOMS, COLLECTION_MESSAGES, COLLECTION_USERS
import json

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
async def send_message(msg: MessageCreate, current_user: dict = Depends(get_current_user)):
    db = get_databases()
    doc_id = ID.unique()

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

        return _doc_to_message(doc)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/messages/{room_id}", response_model=list[MessageResponse])
async def list_messages(
    room_id: str,
    limit: int = QueryParam(50),
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
