from fastapi import APIRouter, HTTPException, Depends, Query as QueryParam
from appwrite.query import Query
from appwrite.id import ID
from auth import get_current_user
from appwrite_client import get_databases
from schemas import ContentCreate, ContentResponse, InteractionCreate, ContentCommentCreate, ContentCommentResponse
from config import APPWRITE_DATABASE_ID, COLLECTION_CONTENT, COLLECTION_INTERACTIONS, COLLECTION_USERS, COLLECTION_CONTENT_COMMENTS
from s3_client import get_s3_client, PRESIGN_EXPIRY
from config import AWS_S3_BUCKET
from moderation import moderate_content, moderate_comment
from strike_system import check_user_ban_status, record_violation
import json
import re
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/content", tags=["Content"])


@router.post("/", response_model=ContentResponse)
async def create_content(content: ContentCreate, current_user: dict = Depends(get_current_user)):
    db = get_databases()
    doc_id = ID.unique()

    # ─── Security Firewall ─────────────────────────────────
    # 1. Ban check
    ban_status = await check_user_ban_status(current_user["sub"])
    if not ban_status["allowed"]:
        raise HTTPException(status_code=403, detail=ban_status["reason"])

    # 2. Content moderation (text + image/video in parallel)
    mod_result = await moderate_content(
        title=content.title,
        body=content.body,
        media_url=content.media_url,
        thumbnail_url=content.thumbnail_url,
    )
    if not mod_result["safe"]:
        # Record strike and escalate
        violation_type = mod_result["violations"][0] if mod_result["violations"] else "policy_violation"
        strike = await record_violation(
            user_id=current_user["sub"],
            violation_type=violation_type,
            details=mod_result.get("details", {}),
            content_type=content.content_type,
            snippet=f"{content.title}: {content.body[:200]}",
        )
        raise HTTPException(
            status_code=400,
            detail=f"Content rejected: {', '.join(mod_result['violations'])}. {strike['message']}"
        )

    # ─── Editorial Gate — basic quality checks ─────────────
    quality_score = 80
    if len(content.body) < 50:
        quality_score -= 20
    if len(content.citations) == 0:
        quality_score -= 10
    if content.domain not in ["technology", "history", "nature", "physics", "ai",
                               "ancient_civilizations", "space", "biology",
                               "chemistry", "mathematics", "philosophy", "engineering"]:
        raise HTTPException(status_code=400, detail="Invalid domain. Must be a knowledge domain.")

    if quality_score < 50:
        raise HTTPException(status_code=400, detail="Content does not meet quality standards (score < 50)")

    try:
        # Get author info
        author = db.get_document(
            database_id=APPWRITE_DATABASE_ID,
            collection_id=COLLECTION_USERS,
            document_id=current_user["sub"]
        )

        doc = db.create_document(
            database_id=APPWRITE_DATABASE_ID,
            collection_id=COLLECTION_CONTENT,
            document_id=doc_id,
            data={
                "title": content.title,
                "body": content.body,
                "content_type": content.content_type,
                "domain": content.domain,
                "author_id": current_user["sub"],
                "author_username": current_user["username"],
                "author_avatar": author.get("avatar_url", ""),
                "thumbnail_url": content.thumbnail_url,
                "media_url": content.media_url,
                "citations": json.dumps(content.citations),
                "tags": json.dumps(content.tags),
                "quality_score": quality_score,
                "likes_count": 0,
                "saves_count": 0,
                "views_count": 0,
                "comments_count": 0,
            }
        )
        return _doc_to_content(doc)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=list[ContentResponse])
async def list_content(
    content_type: str = QueryParam(None),
    domain: str = QueryParam(None),
    limit: int = QueryParam(20, ge=1, le=100),
    offset: int = QueryParam(0, ge=0),
):
    db = get_databases()
    queries = [Query.order_desc("$createdAt"), Query.limit(limit), Query.offset(offset)]

    if content_type:
        queries.append(Query.equal("content_type", content_type))
    if domain:
        queries.append(Query.equal("domain", domain))

    try:
        result = db.list_documents(
            database_id=APPWRITE_DATABASE_ID,
            collection_id=COLLECTION_CONTENT,
            queries=queries
        )
        return [_doc_to_content(d) for d in result["documents"]]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search", response_model=list[ContentResponse])
async def search_content(
    q: str = QueryParam(..., min_length=1),
    limit: int = QueryParam(20, ge=1, le=100),
    offset: int = QueryParam(0, ge=0),
):
    db = get_databases()
    queries = [
        Query.search("title", q),  # Requires full-text index on 'title' if strict, but Appwrite search works on attributes if indexed.
        Query.order_desc("$createdAt"),
        Query.limit(limit),
        Query.offset(offset)
    ]
    try:
        result = db.list_documents(
            database_id=APPWRITE_DATABASE_ID,
            collection_id=COLLECTION_CONTENT,
            queries=queries
        )
        return [_doc_to_content(d) for d in result["documents"]]
    except Exception as e:
        # Fallback to a broader search if full-text index isn't perfectly matched 
        # (Appwrite search requires specific index types). 
        # As a fallback for demo, we can just fetch list and filter locally if query fails,
        # but for production it's better to rely on indexes.
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{content_id}", response_model=ContentResponse)
async def get_content(content_id: str):
    db = get_databases()
    try:
        doc = db.get_document(
            database_id=APPWRITE_DATABASE_ID,
            collection_id=COLLECTION_CONTENT,
            document_id=content_id
        )
        return _doc_to_content(doc)
    except Exception:
        raise HTTPException(status_code=404, detail="Content not found")


@router.post("/{content_id}/interact")
async def interact_with_content(
    content_id: str,
    interaction: InteractionCreate,
    current_user: dict = Depends(get_current_user)
):
    db = get_databases()

    try:
        # Log interaction
        db.create_document(
            database_id=APPWRITE_DATABASE_ID,
            collection_id=COLLECTION_INTERACTIONS,
            document_id=ID.unique(),
            data={
                "user_id": current_user["sub"],
                "content_id": content_id,
                "interaction_type": interaction.interaction_type,
            }
        )

        # Update content counts
        content_doc = db.get_document(
            database_id=APPWRITE_DATABASE_ID,
            collection_id=COLLECTION_CONTENT,
            document_id=content_id
        )

        update_data = {}
        if interaction.interaction_type == "like":
            update_data["likes_count"] = content_doc.get("likes_count", 0) + 1
        elif interaction.interaction_type == "save":
            update_data["saves_count"] = content_doc.get("saves_count", 0) + 1
        elif interaction.interaction_type == "view":
            update_data["views_count"] = content_doc.get("views_count", 0) + 1

        if update_data:
            db.update_document(
                database_id=APPWRITE_DATABASE_ID,
                collection_id=COLLECTION_CONTENT,
                document_id=content_id,
                data=update_data
            )

        return {"status": "ok", "interaction": interaction.interaction_type}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/feed/personalized")
async def get_personalized_feed(
    limit: int = QueryParam(20),
    current_user: dict = Depends(get_current_user)
):
    db = get_databases()

    try:
        user = db.get_document(
            database_id=APPWRITE_DATABASE_ID,
            collection_id=COLLECTION_USERS,
            document_id=current_user["sub"]
        )
        interest_tags = json.loads(user.get("interest_tags", "[]"))

        queries = [Query.order_desc("$createdAt"), Query.limit(limit)]
        if interest_tags:
            queries.append(Query.equal("domain", interest_tags[0]))

        result = db.list_documents(
            database_id=APPWRITE_DATABASE_ID,
            collection_id=COLLECTION_CONTENT,
            queries=queries
        )
        return [_doc_to_content(d) for d in result["documents"]]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{content_id}/comments", response_model=list[ContentCommentResponse])
async def get_content_comments(content_id: str, limit: int = QueryParam(50)):
    db = get_databases()
    try:
        result = db.list_documents(
            database_id=APPWRITE_DATABASE_ID,
            collection_id=COLLECTION_CONTENT_COMMENTS,
            queries=[
                Query.equal("content_id", content_id),
                Query.order_asc("$createdAt"),
                Query.limit(limit)
            ]
        )
        comments = []
        for doc in result["documents"]:
            comments.append(ContentCommentResponse(
                id=doc["$id"],
                content_id=doc.get("content_id", ""),
                user_id=doc.get("user_id", ""),
                username=doc.get("username", ""),
                avatar_url=doc.get("avatar_url", ""),
                body=doc.get("body", ""),
                likes_count=doc.get("likes_count", 0),
                created_at=doc.get("$createdAt", "")
            ))
        return comments
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{content_id}/comments", response_model=ContentCommentResponse)
async def add_content_comment(
    content_id: str,
    comment: ContentCommentCreate,
    current_user: dict = Depends(get_current_user)
):
    db = get_databases()

    # ─── Security Firewall ─────────────────────────────────
    ban_status = await check_user_ban_status(current_user["sub"])
    if not ban_status["allowed"]:
        raise HTTPException(status_code=403, detail=ban_status["reason"])

    mod_result = await moderate_comment(comment.body)
    if not mod_result["safe"]:
        violation_type = mod_result["violations"][0] if mod_result["violations"] else "policy_violation"
        strike = await record_violation(
            user_id=current_user["sub"],
            violation_type=violation_type,
            details=mod_result.get("details", {}),
            content_type="comment",
            snippet=comment.body[:200],
        )
        raise HTTPException(
            status_code=400,
            detail=f"Comment rejected: {', '.join(mod_result['violations'])}. {strike['message']}"
        )

    # Get user to attach avatar/username
    try:
        user = db.get_document(
            database_id=APPWRITE_DATABASE_ID,
            collection_id=COLLECTION_USERS,
            document_id=current_user["sub"]
        )
        
        doc = db.create_document(
            database_id=APPWRITE_DATABASE_ID,
            collection_id=COLLECTION_CONTENT_COMMENTS,
            document_id=ID.unique(),
            data={
                "content_id": content_id,
                "user_id": current_user["sub"],
                "username": current_user["username"],
                "avatar_url": user.get("avatar_url", ""),
                "body": comment.body,
                "likes_count": 0
            }
        )

        # increment content comment count
        content_doc = db.get_document(
            database_id=APPWRITE_DATABASE_ID,
            collection_id=COLLECTION_CONTENT,
            document_id=content_id
        )
        db.update_document(
            database_id=APPWRITE_DATABASE_ID,
            collection_id=COLLECTION_CONTENT,
            document_id=content_id,
            data={"comments_count": content_doc.get("comments_count", 0) + 1}
        )

        return ContentCommentResponse(
            id=doc["$id"],
            content_id=doc.get("content_id", ""),
            user_id=doc.get("user_id", ""),
            username=doc.get("username", ""),
            avatar_url=doc.get("avatar_url", ""),
            body=doc.get("body", ""),
            likes_count=doc.get("likes_count", 0),
            created_at=doc.get("$createdAt", "")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _refresh_s3_url(url: str) -> str:
    """Extract S3 key from a presigned/direct URL and generate a fresh presigned URL."""
    if not url or url.startswith("blob:") or "s3" not in url and "amazonaws" not in url:
        return url
    try:
        # Extract the key from URL: bucket.s3.region.amazonaws.com/KEY?... or s3.region.../bucket/KEY?...
        match = re.search(r'amazonaws\.com/([^?]+)', url)
        if not match:
            return url
        key = match.group(1)
        # Remove bucket prefix if present
        if key.startswith(AWS_S3_BUCKET + "/"):
            key = key[len(AWS_S3_BUCKET) + 1:]
        s3 = get_s3_client()
        return s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": AWS_S3_BUCKET, "Key": key},
            ExpiresIn=PRESIGN_EXPIRY,
        )
    except Exception as e:
        logger.warning(f"Failed to refresh S3 URL: {e}")
        return url


def _doc_to_content(doc: dict) -> ContentResponse:
    media_url = doc.get("media_url", "")
    thumbnail_url = doc.get("thumbnail_url", "")

    # Refresh S3 presigned URLs so they don't expire
    if media_url and "amazonaws" in media_url:
        media_url = _refresh_s3_url(media_url)
    if thumbnail_url and "amazonaws" in thumbnail_url:
        thumbnail_url = _refresh_s3_url(thumbnail_url)

    return ContentResponse(
        id=doc["$id"],
        title=doc.get("title", ""),
        body=doc.get("body", ""),
        content_type=doc.get("content_type", ""),
        domain=doc.get("domain", ""),
        author_id=doc.get("author_id", ""),
        author_username=doc.get("author_username", ""),
        author_avatar=doc.get("author_avatar", ""),
        thumbnail_url=thumbnail_url,
        media_url=media_url,
        citations=json.loads(doc.get("citations", "[]")),
        tags=json.loads(doc.get("tags", "[]")),
        quality_score=doc.get("quality_score", 80),
        likes_count=doc.get("likes_count", 0),
        saves_count=doc.get("saves_count", 0),
        views_count=doc.get("views_count", 0),
        comments_count=doc.get("comments_count", 0),
        created_at=doc.get("$createdAt", ""),
    )
