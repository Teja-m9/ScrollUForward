"""
Auth Service — port 8001
========================
Handles: register, login, Google OAuth, token validation, /me
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

import json, logging
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from appwrite.id import ID
from appwrite.query import Query

from shared.config import APPWRITE_DATABASE_ID, COLLECTION_USERS
from shared.appwrite_client import get_databases
from shared.auth import (
    hash_password, verify_password, create_access_token, get_current_user
)

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [AUTH] %(message)s")
log = logging.getLogger("auth_service")

app = FastAPI(title="Auth Service", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])


# ── Schemas ───────────────────────────────────────────────────────────────────
class RegisterRequest(BaseModel):
    username:     str
    email:        str
    password:     str
    display_name: str = ""
    interest_tags: list[str] = []

class LoginRequest(BaseModel):
    email:    str
    password: str

class GoogleAuthRequest(BaseModel):
    id_token:    str = ""
    access_token: str = ""
    email:       str = ""
    display_name: str = ""
    google_id:   str = ""

class TokenResponse(BaseModel):
    access_token: str
    token_type:   str = "bearer"
    user_id:      str
    username:     str


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"service": "auth", "status": "up"}


@app.post("/auth/register", response_model=TokenResponse)
async def register(req: RegisterRequest):
    db = get_databases()

    # Check duplicate email
    try:
        existing = db.list_documents(
            database_id=APPWRITE_DATABASE_ID,
            collection_id=COLLECTION_USERS,
            queries=[Query.equal("email", req.email), Query.limit(1)],
        )
        if existing["total"] > 0:
            raise HTTPException(status_code=400, detail="Email already registered")
    except HTTPException:
        raise
    except Exception:
        pass

    user_id     = ID.unique()
    hashed_pass = hash_password(req.password)

    try:
        db.create_document(
            database_id=APPWRITE_DATABASE_ID,
            collection_id=COLLECTION_USERS,
            document_id=user_id,
            data={
                "username":       req.username,
                "email":          req.email,
                "password_hash":  hashed_pass,
                "display_name":   req.display_name or req.username,
                "bio":            "",
                "avatar_url":     "",
                "interest_tags":  json.dumps(req.interest_tags),
                "iq_score":       0,
                "followers_count": 0,
                "following_count": 0,
                "posts_count":    0,
                "streak_days":    0,
                "badges":         json.dumps([]),
                "is_banned":      False,
                "ban_type":       "",
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    token = create_access_token(user_id, req.username, req.email)
    log.info(f"Registered: {req.username} ({user_id})")
    return TokenResponse(access_token=token, user_id=user_id, username=req.username)


@app.post("/auth/login", response_model=TokenResponse)
async def login(req: LoginRequest):
    db = get_databases()

    try:
        result = db.list_documents(
            database_id=APPWRITE_DATABASE_ID,
            collection_id=COLLECTION_USERS,
            queries=[Query.equal("email", req.email), Query.limit(1)],
        )
        docs = result["documents"]
        if not docs:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        user = docs[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    if not verify_password(req.password, user.get("password_hash", "")):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if user.get("is_banned") and user.get("ban_type") == "permanent":
        raise HTTPException(status_code=403, detail="Account permanently banned")

    token = create_access_token(user["$id"], user["username"], user["email"])
    log.info(f"Login: {user['username']}")
    return TokenResponse(access_token=token, user_id=user["$id"], username=user["username"])


@app.post("/auth/google", response_model=TokenResponse)
async def google_auth(req: GoogleAuthRequest):
    """Google OAuth — verify token, create or retrieve user."""
    import httpx
    db = get_databases()

    # Verify with Google
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get(
                "https://www.googleapis.com/oauth2/v3/userinfo",
                headers={"Authorization": f"Bearer {req.access_token}"},
                timeout=10,
            )
            if r.status_code != 200:
                raise HTTPException(status_code=401, detail="Invalid Google token")
            info = r.json()
            email        = info.get("email", req.email)
            display_name = info.get("name", req.display_name)
            google_id    = info.get("sub", req.google_id)
    except HTTPException:
        raise
    except Exception:
        # Fallback: trust the client-provided values (implicit flow)
        email        = req.email
        display_name = req.display_name
        google_id    = req.google_id

    if not email:
        raise HTTPException(status_code=400, detail="Could not get email from Google")

    # Find or create user
    try:
        result = db.list_documents(
            database_id=APPWRITE_DATABASE_ID,
            collection_id=COLLECTION_USERS,
            queries=[Query.equal("email", email), Query.limit(1)],
        )
        docs = result["documents"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    if docs:
        user = docs[0]
    else:
        user_id  = ID.unique()
        username = email.split("@")[0].replace(".", "_")
        try:
            user = db.create_document(
                database_id=APPWRITE_DATABASE_ID,
                collection_id=COLLECTION_USERS,
                document_id=user_id,
                data={
                    "username":       username,
                    "email":          email,
                    "password_hash":  "",
                    "display_name":   display_name or username,
                    "bio":            "",
                    "avatar_url":     "",
                    "interest_tags":  json.dumps([]),
                    "iq_score":       0,
                    "followers_count": 0,
                    "following_count": 0,
                    "posts_count":    0,
                    "streak_days":    0,
                    "badges":         json.dumps([]),
                    "is_banned":      False,
                    "ban_type":       "",
                    "google_id":      google_id,
                },
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    token = create_access_token(user["$id"], user["username"], email)
    log.info(f"Google auth: {user['username']}")
    return TokenResponse(access_token=token, user_id=user["$id"], username=user["username"])


@app.get("/auth/me")
async def me(current_user: dict = Depends(get_current_user)):
    """Return the decoded JWT payload (user info)."""
    return {
        "user_id":  current_user["sub"],
        "username": current_user.get("username"),
        "email":    current_user.get("email"),
    }


@app.post("/auth/validate")
async def validate_token(current_user: dict = Depends(get_current_user)):
    """Used by other services to validate a JWT without re-implementing decode."""
    return {"valid": True, "user": current_user}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
