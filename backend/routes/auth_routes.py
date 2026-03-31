from fastapi import APIRouter, HTTPException, Depends, Query as QueryParam
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from appwrite.query import Query
from appwrite.id import ID
from auth import hash_password, verify_password, create_access_token, get_current_user
from appwrite_client import get_databases
from schemas import RegisterRequest, LoginRequest, TokenResponse
from config import APPWRITE_DATABASE_ID, COLLECTION_USERS, GOOGLE_CLIENT_ID_WEB, GOOGLE_CLIENT_ID_ANDROID
import json, httpx, logging

logger = logging.getLogger("scrolluforward")

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


# ─── Google OAuth ─────────────────────────────────────────

class GoogleAuthRequest(BaseModel):
    id_token: str = ""
    code: str = ""
    redirect_uri: str = ""


@router.post("/google", response_model=TokenResponse)
async def google_auth(req: GoogleAuthRequest):
    """Verify Google ID token or exchange auth code, then create/login user."""
    from config import GOOGLE_CLIENT_SECRET

    google_user = None

    # Method 1: Exchange authorization code for tokens
    if req.code:
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                token_resp = await client.post(
                    "https://oauth2.googleapis.com/token",
                    data={
                        "code": req.code,
                        "client_id": GOOGLE_CLIENT_ID_WEB,
                        "client_secret": GOOGLE_CLIENT_SECRET,
                        "redirect_uri": req.redirect_uri,
                        "grant_type": "authorization_code",
                    },
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )
                if token_resp.status_code != 200:
                    logger.error(f"[GoogleAuth] Token exchange failed: {token_resp.text}")
                    raise HTTPException(status_code=401, detail="Failed to exchange Google code")

                tokens = token_resp.json()
                id_token = tokens.get("id_token", "")

                # Verify the id_token
                info_resp = await client.get(
                    f"https://oauth2.googleapis.com/tokeninfo?id_token={id_token}"
                )
                if info_resp.status_code != 200:
                    raise HTTPException(status_code=401, detail="Invalid Google token")
                google_user = info_resp.json()
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"[GoogleAuth] Code exchange error: {e}")
            raise HTTPException(status_code=401, detail="Google authentication failed")

    # Method 2: Direct ID token verification
    elif req.id_token:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    f"https://oauth2.googleapis.com/tokeninfo?id_token={req.id_token}"
                )
                if resp.status_code != 200:
                    raise HTTPException(status_code=401, detail="Invalid Google token")
                google_user = resp.json()
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"[GoogleAuth] Token verification failed: {e}")
            raise HTTPException(status_code=401, detail="Failed to verify Google token")
    else:
        raise HTTPException(status_code=400, detail="Provide either id_token or code")

    email = google_user.get("email", "")
    name = google_user.get("name", "")
    picture = google_user.get("picture", "")
    google_sub = google_user.get("sub", "")

    if not email:
        raise HTTPException(status_code=400, detail="No email in Google token")

    db = get_databases()

    # Check if user exists by email
    try:
        existing = db.list_documents(
            database_id=APPWRITE_DATABASE_ID,
            collection_id=COLLECTION_USERS,
            queries=[Query.equal("email", email)]
        )

        if existing["total"] > 0:
            # User exists — login
            user = existing["documents"][0]
            token = create_access_token(user["$id"], user["username"])
            logger.info(f"[GoogleAuth] Login: {email}")
            return TokenResponse(
                access_token=token,
                user_id=user["$id"],
                username=user["username"],
            )
    except Exception as e:
        logger.error(f"[GoogleAuth] DB lookup error: {e}")

    # User doesn't exist — create new account
    user_id = ID.unique()
    username = email.split("@")[0].replace(".", "_").lower()[:20]

    # Ensure username is unique
    try:
        uname_check = db.list_documents(
            database_id=APPWRITE_DATABASE_ID,
            collection_id=COLLECTION_USERS,
            queries=[Query.equal("username", username)]
        )
        if uname_check["total"] > 0:
            username = username + "_" + google_sub[-4:]
    except Exception:
        pass

    try:
        db.create_document(
            database_id=APPWRITE_DATABASE_ID,
            collection_id=COLLECTION_USERS,
            document_id=user_id,
            data={
                "username": username,
                "email": email,
                "password_hash": "",  # No password for Google users
                "display_name": name or username,
                "bio": "",
                "avatar_url": picture,
                "iq_score": 0,
                "knowledge_rank": "Novice",
                "interest_tags": json.dumps([]),
                "followers_count": 0,
                "following_count": 0,
                "posts_count": 0,
                "streak_days": 0,
                "badges": json.dumps(["google_user"]),
            }
        )
        logger.info(f"[GoogleAuth] New user: {email} -> {username}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create user: {str(e)}")

    token = create_access_token(user_id, username)
    return TokenResponse(
        access_token=token,
        user_id=user_id,
        username=username,
    )


@router.get("/google/callback")
async def google_callback(code: str = QueryParam(...)):
    """Google OAuth callback — exchanges code and redirects back to app with token."""
    from config import GOOGLE_CLIENT_SECRET
    redirect_uri = "https://scrolluforward-production.up.railway.app/auth/google/callback"

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            # Exchange code for tokens
            token_resp = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "code": code,
                    "client_id": GOOGLE_CLIENT_ID_WEB,
                    "client_secret": GOOGLE_CLIENT_SECRET,
                    "redirect_uri": redirect_uri,
                    "grant_type": "authorization_code",
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            if token_resp.status_code != 200:
                logger.error(f"[GoogleCallback] Token exchange failed: {token_resp.text}")
                return RedirectResponse(url=f"scrolluforward://auth?error=token_exchange_failed")

            tokens = token_resp.json()
            id_token = tokens.get("id_token", "")

            # Verify id_token
            info_resp = await client.get(f"https://oauth2.googleapis.com/tokeninfo?id_token={id_token}")
            if info_resp.status_code != 200:
                return RedirectResponse(url=f"scrolluforward://auth?error=invalid_token")

            google_user = info_resp.json()

    except Exception as e:
        logger.error(f"[GoogleCallback] Error: {e}")
        return RedirectResponse(url=f"scrolluforward://auth?error=server_error")

    email = google_user.get("email", "")
    name = google_user.get("name", "")
    picture = google_user.get("picture", "")
    google_sub = google_user.get("sub", "")

    if not email:
        return RedirectResponse(url=f"scrolluforward://auth?error=no_email")

    db = get_databases()

    # Check if user exists
    try:
        existing = db.list_documents(
            database_id=APPWRITE_DATABASE_ID,
            collection_id=COLLECTION_USERS,
            queries=[Query.equal("email", email)]
        )
        if existing["total"] > 0:
            user = existing["documents"][0]
            jwt_token = create_access_token(user["$id"], user["username"])
            logger.info(f"[GoogleCallback] Login: {email}")
            return RedirectResponse(
                url=f"scrolluforward://auth?token={jwt_token}&user_id={user['$id']}&username={user['username']}"
            )
    except Exception as e:
        logger.error(f"[GoogleCallback] DB error: {e}")

    # Create new user
    user_id = ID.unique()
    username = email.split("@")[0].replace(".", "_").lower()[:20]

    try:
        uname_check = db.list_documents(
            database_id=APPWRITE_DATABASE_ID,
            collection_id=COLLECTION_USERS,
            queries=[Query.equal("username", username)]
        )
        if uname_check["total"] > 0:
            username = username + "_" + google_sub[-4:]
    except Exception:
        pass

    try:
        db.create_document(
            database_id=APPWRITE_DATABASE_ID,
            collection_id=COLLECTION_USERS,
            document_id=user_id,
            data={
                "username": username,
                "email": email,
                "password_hash": "",
                "display_name": name or username,
                "bio": "",
                "avatar_url": picture,
                "iq_score": 0,
                "knowledge_rank": "Novice",
                "interest_tags": json.dumps([]),
                "followers_count": 0,
                "following_count": 0,
                "posts_count": 0,
                "streak_days": 0,
                "badges": json.dumps(["google_user"]),
            }
        )
        logger.info(f"[GoogleCallback] New user: {email} -> {username}")
    except Exception as e:
        logger.error(f"[GoogleCallback] Create user failed: {e}")
        return RedirectResponse(url=f"scrolluforward://auth?error=create_failed")

    jwt_token = create_access_token(user_id, username)
    return RedirectResponse(
        url=f"scrolluforward://auth?token={jwt_token}&user_id={user_id}&username={username}"
    )
