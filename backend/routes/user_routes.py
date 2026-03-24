from fastapi import APIRouter, HTTPException, Depends
from appwrite.query import Query
from appwrite.id import ID
from auth import get_current_user
from appwrite_client import get_databases
from schemas import IQUpdate, LeaderboardEntry, UpdateProfileRequest
from config import (
    APPWRITE_DATABASE_ID, COLLECTION_USERS, COLLECTION_INTERACTIONS, IQ_POINTS
)
import json

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
    if user_id == current_user["sub"]:
        raise HTTPException(status_code=400, detail="Cannot follow yourself")

    try:
        # Update target's followers count
        target = db.get_document(
            database_id=APPWRITE_DATABASE_ID,
            collection_id=COLLECTION_USERS,
            document_id=user_id
        )
        db.update_document(
            database_id=APPWRITE_DATABASE_ID,
            collection_id=COLLECTION_USERS,
            document_id=user_id,
            data={"followers_count": target.get("followers_count", 0) + 1}
        )

        # Update current user's following count
        me = db.get_document(
            database_id=APPWRITE_DATABASE_ID,
            collection_id=COLLECTION_USERS,
            document_id=current_user["sub"]
        )
        db.update_document(
            database_id=APPWRITE_DATABASE_ID,
            collection_id=COLLECTION_USERS,
            document_id=current_user["sub"],
            data={"following_count": me.get("following_count", 0) + 1}
        )

        return {"status": "followed", "user_id": user_id}
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
