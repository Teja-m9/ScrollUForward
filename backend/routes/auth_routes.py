from fastapi import APIRouter, HTTPException, Depends, Query as QueryParam
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from appwrite.query import Query
from appwrite.id import ID
from auth import hash_password, verify_password, create_access_token, get_current_user
from appwrite_client import get_databases
from schemas import RegisterRequest, LoginRequest, TokenResponse
from config import APPWRITE_DATABASE_ID, COLLECTION_USERS, GOOGLE_CLIENT_ID_WEB, GOOGLE_CLIENT_ID_ANDROID, GOOGLE_CLIENT_SECRET
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
async def google_callback(code: str = QueryParam(None), id_token: str = QueryParam(None)):
    """Google OAuth callback — handles both code exchange and id_token implicit flow."""
    from fastapi.responses import HTMLResponse

    # If no code and no id_token in query, serve a page that reads the fragment
    if not code and not id_token:
        # Google implicit flow sends id_token in URL fragment (#id_token=...)
        # Fragments aren't sent to server, so serve JS that reads it and redirects
        return HTMLResponse(content="""
        <html><head><style>
        body{background:#0a0a0a;color:#fff;font-family:sans-serif;display:flex;justify-content:center;align-items:center;height:100vh;margin:0;flex-direction:column}
        .spinner{width:40px;height:40px;border:4px solid #333;border-top:4px solid #AAFF00;border-radius:50%;animation:spin 1s linear infinite}
        @keyframes spin{to{transform:rotate(360deg)}}
        p{margin-top:20px;color:#888}
        .success{color:#AAFF00;font-size:18px;margin-top:20px}
        </style></head><body>
        <div class="spinner"></div>
        <p id="status">Signing you in...</p>
        <script>
        var hash = window.location.hash.substring(1);
        var params = new URLSearchParams(hash);
        var idToken = params.get('id_token');
        if (idToken) {
            document.getElementById('status').innerHTML = '<span class="success">✓ Authenticated! Redirecting to app...</span>';
            window.location.href = 'scrolluforward://auth?id_token=' + idToken;
            setTimeout(function(){
                document.getElementById('status').innerHTML = '<span class="success">✓ Success! Open ScrollUForward app on your phone.</span><br><br><small style="color:#555">If the app didn\\'t open, copy this and use in the app.</small>';
            }, 2000);
        } else {
            var q = window.location.search;
            if (q) {
                window.location.href = 'scrolluforward://auth' + q;
            } else {
                document.getElementById('status').textContent = 'Waiting for Google...';
            }
        }
        </script></body></html>
        """)

    redirect_uri = "https://scrolluforward-production.up.railway.app/auth/google/callback"

    # If we got an id_token directly, verify and create user
    if id_token:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                info_resp = await client.get(f"https://oauth2.googleapis.com/tokeninfo?id_token={id_token}")
                if info_resp.status_code == 200:
                    google_user = info_resp.json()
                    # Process user (reuse logic below)
                    email = google_user.get("email", "")
                    name = google_user.get("name", "")
                    picture = google_user.get("picture", "")
                    google_sub = google_user.get("sub", "")
                    if email:
                        db = get_databases()
                        existing = db.list_documents(APPWRITE_DATABASE_ID, COLLECTION_USERS, queries=[Query.equal("email", email)])
                        if existing["total"] > 0:
                            user = existing["documents"][0]
                            jwt_token = create_access_token(user["$id"], user["username"])
                            return RedirectResponse(url=f"scrolluforward://auth?token={jwt_token}&user_id={user['$id']}&username={user['username']}")
                        # Create new user
                        user_id = ID.unique()
                        username = email.split("@")[0].replace(".", "_").lower()[:20]
                        db.create_document(APPWRITE_DATABASE_ID, COLLECTION_USERS, document_id=user_id, data={
                            "username": username, "email": email, "password_hash": "", "display_name": name or username,
                            "bio": "", "avatar_url": picture, "iq_score": 0, "knowledge_rank": "Novice",
                            "interest_tags": json.dumps([]), "followers_count": 0, "following_count": 0,
                            "posts_count": 0, "streak_days": 0, "badges": json.dumps(["google_user"]),
                        })
                        jwt_token = create_access_token(user_id, username)
                        return RedirectResponse(url=f"scrolluforward://auth?token={jwt_token}&user_id={user_id}&username={username}")
        except Exception as e:
            logger.error(f"[GoogleCallback] id_token processing failed: {e}")
        return RedirectResponse(url="scrolluforward://auth?error=token_verification_failed")

    logger.info(f"[GoogleCallback] Got code={code[:10]}..., client_id={GOOGLE_CLIENT_ID_WEB[:20]}..., secret={'SET' if GOOGLE_CLIENT_SECRET else 'EMPTY'}")

    try:
        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
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
                err_detail = token_resp.text[:200]
                logger.error(f"[GoogleCallback] Token exchange failed ({token_resp.status_code}): {err_detail}")
                return RedirectResponse(url=f"scrolluforward://auth?error=token_exchange_failed&detail={token_resp.status_code}")

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
