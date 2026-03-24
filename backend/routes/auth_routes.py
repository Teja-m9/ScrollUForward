from fastapi import APIRouter, HTTPException, Depends
from appwrite.query import Query
from appwrite.id import ID
from auth import hash_password, verify_password, create_access_token, get_current_user
from appwrite_client import get_databases
from schemas import RegisterRequest, LoginRequest, TokenResponse
from config import APPWRITE_DATABASE_ID, COLLECTION_USERS
import json

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse)
async def register(req: RegisterRequest):
    db = get_databases()

    # Check if user already exists
    try:
        existing = db.list_documents(
            database_id=APPWRITE_DATABASE_ID,
            collection_id=COLLECTION_USERS,
            queries=[Query.equal("email", req.email)]
        )
        if existing["total"] > 0:
            raise HTTPException(status_code=400, detail="Email already registered")
    except HTTPException:
        raise
    except Exception:
        pass  # Collection might not exist yet

    # Create user document
    user_id = ID.unique()
    hashed_pw = hash_password(req.password)

    try:
        user_doc = db.create_document(
            database_id=APPWRITE_DATABASE_ID,
            collection_id=COLLECTION_USERS,
            document_id=user_id,
            data={
                "username": req.username,
                "email": req.email,
                "password_hash": hashed_pw,
                "display_name": req.display_name or req.username,
                "bio": "",
                "avatar_url": "",
                "iq_score": 0,
                "knowledge_rank": "Novice",
                "interest_tags": json.dumps([]),
                "followers_count": 0,
                "following_count": 0,
                "posts_count": 0,
                "streak_days": 0,
                "badges": json.dumps([]),
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create user: {str(e)}")

    token = create_access_token(user_id, req.username)
    return TokenResponse(
        access_token=token,
        user_id=user_id,
        username=req.username,
    )


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest):
    db = get_databases()

    try:
        result = db.list_documents(
            database_id=APPWRITE_DATABASE_ID,
            collection_id=COLLECTION_USERS,
            queries=[Query.equal("email", req.email)]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    if result["total"] == 0:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    user = result["documents"][0]

    if not verify_password(req.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token(user["$id"], user["username"])
    return TokenResponse(
        access_token=token,
        user_id=user["$id"],
        username=user["username"],
    )


@router.get("/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    db = get_databases()
    try:
        user = db.get_document(
            database_id=APPWRITE_DATABASE_ID,
            collection_id=COLLECTION_USERS,
            document_id=current_user["sub"]
        )
        return {
            "user_id": user["$id"],
            "username": user["username"],
            "display_name": user.get("display_name", ""),
            "email": user.get("email", ""),
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
    except Exception as e:
        raise HTTPException(status_code=404, detail="User not found")
