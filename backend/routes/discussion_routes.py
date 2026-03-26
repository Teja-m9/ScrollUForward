from fastapi import APIRouter, HTTPException, Depends, Query as QueryParam
from appwrite.query import Query
from appwrite.id import ID
from auth import get_current_user
from appwrite_client import get_databases
from schemas import DiscussionCreate, DiscussionResponse, CommentCreate, CommentResponse
from config import APPWRITE_DATABASE_ID, COLLECTION_DISCUSSIONS, COLLECTION_COMMENTS, COLLECTION_USERS
from moderation import moderate_content, moderate_comment
from strike_system import check_user_ban_status, record_violation
import json

router = APIRouter(prefix="/discussions", tags=["Discussions"])


@router.post("/", response_model=DiscussionResponse)
async def create_discussion(disc: DiscussionCreate, current_user: dict = Depends(get_current_user)):
    db = get_databases()
    doc_id = ID.unique()

    # ─── Security Firewall ─────────────────────────────────
    ban_status = await check_user_ban_status(current_user["sub"])
    if not ban_status["allowed"]:
        raise HTTPException(status_code=403, detail=ban_status["reason"])

    mod_result = await moderate_content(title=disc.title, body=disc.description)
    if not mod_result["safe"]:
        violation_type = mod_result["violations"][0] if mod_result["violations"] else "policy_violation"
        strike = await record_violation(
            user_id=current_user["sub"], violation_type=violation_type,
            details=mod_result.get("details", {}), content_type="discussion",
            snippet=f"{disc.title}: {disc.description[:200]}",
        )
        raise HTTPException(status_code=400, detail=f"Discussion rejected: {', '.join(mod_result['violations'])}. {strike['message']}")

    try:
        author = db.get_document(
            database_id=APPWRITE_DATABASE_ID,
            collection_id=COLLECTION_USERS,
            document_id=current_user["sub"]
        )

        doc = db.create_document(
            database_id=APPWRITE_DATABASE_ID,
            collection_id=COLLECTION_DISCUSSIONS,
            document_id=doc_id,
            data={
                "title": disc.title,
                "description": disc.description,
                "domain": disc.domain,
                "creator_id": current_user["sub"],
                "creator_username": current_user["username"],
                "creator_avatar": author.get("avatar_url", ""),
                "tags": json.dumps(disc.tags),
                "comments_count": 0,
                "participants_count": 1,
            }
        )
        return _doc_to_discussion(doc)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=list[DiscussionResponse])
async def list_discussions(
    domain: str = QueryParam(None),
    limit: int = QueryParam(20, ge=1, le=100),
    offset: int = QueryParam(0),
):
    db = get_databases()
    queries = [Query.order_desc("$createdAt"), Query.limit(limit), Query.offset(offset)]
    if domain:
        queries.append(Query.equal("domain", domain))

    try:
        result = db.list_documents(
            database_id=APPWRITE_DATABASE_ID,
            collection_id=COLLECTION_DISCUSSIONS,
            queries=queries
        )
        return [_doc_to_discussion(d) for d in result["documents"]]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{discussion_id}", response_model=DiscussionResponse)
async def get_discussion(discussion_id: str):
    db = get_databases()
    try:
        doc = db.get_document(
            database_id=APPWRITE_DATABASE_ID,
            collection_id=COLLECTION_DISCUSSIONS,
            document_id=discussion_id
        )
        return _doc_to_discussion(doc)
    except Exception:
        raise HTTPException(status_code=404, detail="Discussion not found")


# ─── Comments ────────────────────────────────────────────────

@router.post("/{discussion_id}/comments", response_model=CommentResponse)
async def create_comment(
    discussion_id: str,
    comment: CommentCreate,
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
            user_id=current_user["sub"], violation_type=violation_type,
            details=mod_result.get("details", {}), content_type="comment",
            snippet=comment.body[:200],
        )
        raise HTTPException(status_code=400, detail=f"Comment rejected: {', '.join(mod_result['violations'])}. {strike['message']}")

    try:
        author = db.get_document(
            database_id=APPWRITE_DATABASE_ID,
            collection_id=COLLECTION_USERS,
            document_id=current_user["sub"]
        )

        doc = db.create_document(
            database_id=APPWRITE_DATABASE_ID,
            collection_id=COLLECTION_COMMENTS,
            document_id=ID.unique(),
            data={
                "discussion_id": discussion_id,
                "user_id": current_user["sub"],
                "username": current_user["username"],
                "avatar_url": author.get("avatar_url", ""),
                "body": comment.body,
                "citation_url": comment.citation_url,
                "likes_count": 0,
            }
        )

        # Update comment count
        disc = db.get_document(
            database_id=APPWRITE_DATABASE_ID,
            collection_id=COLLECTION_DISCUSSIONS,
            document_id=discussion_id
        )
        db.update_document(
            database_id=APPWRITE_DATABASE_ID,
            collection_id=COLLECTION_DISCUSSIONS,
            document_id=discussion_id,
            data={"comments_count": disc.get("comments_count", 0) + 1}
        )

        return _doc_to_comment(doc)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{discussion_id}/comments", response_model=list[CommentResponse])
async def list_comments(discussion_id: str, limit: int = QueryParam(50)):
    db = get_databases()
    try:
        result = db.list_documents(
            database_id=APPWRITE_DATABASE_ID,
            collection_id=COLLECTION_COMMENTS,
            queries=[
                Query.equal("discussion_id", discussion_id),
                Query.order_desc("$createdAt"),
                Query.limit(limit),
            ]
        )
        return [_doc_to_comment(d) for d in result["documents"]]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _doc_to_discussion(doc: dict) -> DiscussionResponse:
    return DiscussionResponse(
        id=doc["$id"],
        title=doc.get("title", ""),
        description=doc.get("description", ""),
        domain=doc.get("domain", ""),
        creator_id=doc.get("creator_id", ""),
        creator_username=doc.get("creator_username", ""),
        creator_avatar=doc.get("creator_avatar", ""),
        tags=json.loads(doc.get("tags", "[]")),
        comments_count=doc.get("comments_count", 0),
        participants_count=doc.get("participants_count", 0),
        created_at=doc.get("$createdAt", ""),
    )


def _doc_to_comment(doc: dict) -> CommentResponse:
    return CommentResponse(
        id=doc["$id"],
        discussion_id=doc.get("discussion_id", ""),
        user_id=doc.get("user_id", ""),
        username=doc.get("username", ""),
        avatar_url=doc.get("avatar_url", ""),
        body=doc.get("body", ""),
        citation_url=doc.get("citation_url", ""),
        likes_count=doc.get("likes_count", 0),
        created_at=doc.get("$createdAt", ""),
    )
