"""
Admin Routes — View violations, manage bans.
"""
from fastapi import APIRouter, HTTPException, Depends
from appwrite.query import Query
from auth import get_current_user
from appwrite_client import get_databases
from strike_system import get_user_violations
from config import APPWRITE_DATABASE_ID, COLLECTION_USERS, COLLECTION_USER_VIOLATIONS

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/violations")
async def list_all_violations(limit: int = 50):
    """List recent violations across all users."""
    db = get_databases()
    try:
        result = db.list_documents(
            database_id=APPWRITE_DATABASE_ID,
            collection_id=COLLECTION_USER_VIOLATIONS,
            queries=[
                Query.order_desc("$createdAt"),
                Query.limit(limit),
            ],
        )
        return [
            {
                "id": doc["$id"],
                "user_id": doc.get("user_id", ""),
                "violation_type": doc.get("violation_type", ""),
                "content_type": doc.get("content_type", ""),
                "severity": doc.get("severity", ""),
                "content_snippet": doc.get("content_snippet", ""),
                "created_at": doc.get("$createdAt", ""),
            }
            for doc in result["documents"]
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/violations/{user_id}")
async def list_user_violations(user_id: str):
    """Get violation history for a specific user."""
    violations = await get_user_violations(user_id)
    return violations


@router.post("/users/{user_id}/ban")
async def ban_user(user_id: str):
    """Manually ban a user."""
    db = get_databases()
    try:
        db.update_document(
            database_id=APPWRITE_DATABASE_ID,
            collection_id=COLLECTION_USERS,
            document_id=user_id,
            data={"is_banned": True},
        )
        return {"status": "banned", "user_id": user_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/users/{user_id}/unban")
async def unban_user(user_id: str):
    """Manually unban a user and reset strikes."""
    db = get_databases()
    try:
        db.update_document(
            database_id=APPWRITE_DATABASE_ID,
            collection_id=COLLECTION_USERS,
            document_id=user_id,
            data={
                "is_banned": False,
                "ban_until": "",
                "strike_count": 0,
            },
        )
        return {"status": "unbanned", "user_id": user_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
