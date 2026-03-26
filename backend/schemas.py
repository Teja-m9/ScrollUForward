from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ─── Auth ────────────────────────────────────────────────────
class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=30)
    email: str
    password: str = Field(..., min_length=6)
    display_name: str = ""


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    username: str


# ─── User / Profile ─────────────────────────────────────────
class UserProfile(BaseModel):
    user_id: str
    username: str
    display_name: str = ""
    bio: str = ""
    avatar_url: str = ""
    iq_score: int = 0
    knowledge_rank: str = "Novice"
    interest_tags: List[str] = []
    followers_count: int = 0
    following_count: int = 0
    posts_count: int = 0
    streak_days: int = 0
    badges: List[str] = []


class UpdateProfileRequest(BaseModel):
    display_name: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    interest_tags: Optional[List[str]] = None


# ─── Content ─────────────────────────────────────────────────
class ContentCreate(BaseModel):
    title: str
    body: str
    content_type: str  # reel, article, news
    domain: str  # technology, history, nature
    thumbnail_url: str = ""
    media_url: str = ""
    citations: List[str] = []
    tags: List[str] = []


class ContentResponse(BaseModel):
    id: str
    title: str
    body: str
    content_type: str
    domain: str
    author_id: str
    author_username: str = ""
    author_avatar: str = ""
    thumbnail_url: str = ""
    media_url: str = ""
    citations: List[str] = []
    tags: List[str] = []
    quality_score: int = 80
    likes_count: int = 0
    saves_count: int = 0
    views_count: int = 0
    comments_count: int = 0
    created_at: str = ""
    is_liked: bool = False
    is_saved: bool = False


# ─── Interactions ────────────────────────────────────────────
class InteractionCreate(BaseModel):
    content_id: str
    interaction_type: str  # like, save, view, share


# ─── Content Comments ───────────────────────────────────────
class ContentCommentCreate(BaseModel):
    body: str

class ContentCommentResponse(BaseModel):
    id: str
    content_id: str
    user_id: str
    username: str = ""
    avatar_url: str = ""
    body: str
    likes_count: int = 0
    created_at: str = ""


# ─── Discussions ─────────────────────────────────────────────
class DiscussionCreate(BaseModel):
    title: str
    description: str
    domain: str
    tags: List[str] = []


class DiscussionResponse(BaseModel):
    id: str
    title: str
    description: str
    domain: str
    creator_id: str
    creator_username: str = ""
    creator_avatar: str = ""
    tags: List[str] = []
    comments_count: int = 0
    participants_count: int = 0
    created_at: str = ""


class CommentCreate(BaseModel):
    body: str
    citation_url: str = ""


class CommentResponse(BaseModel):
    id: str
    discussion_id: str
    user_id: str
    username: str = ""
    avatar_url: str = ""
    body: str
    citation_url: str = ""
    likes_count: int = 0
    created_at: str = ""


# ─── Chat / Messaging ───────────────────────────────────────
class ChatRoomCreate(BaseModel):
    participant_ids: List[str]
    is_group: bool = False
    name: str = ""


class ChatRoomResponse(BaseModel):
    id: str
    participants: List[str] = []
    is_group: bool = False
    name: str = ""
    last_message: str = ""
    last_message_time: str = ""
    unread_count: int = 0


class MessageCreate(BaseModel):
    chat_room_id: str
    body: str
    message_type: str = "text"  # text, image, link


class MessageResponse(BaseModel):
    id: str
    chat_room_id: str
    sender_id: str
    sender_username: str = ""
    sender_avatar: str = ""
    body: str
    message_type: str = "text"
    created_at: str = ""
    is_read: bool = False


# ─── IQ / Leaderboard ───────────────────────────────────────
class IQUpdate(BaseModel):
    action: str  # watch_reel, read_article, complete_quiz, etc.
    content_id: str = ""


class LeaderboardEntry(BaseModel):
    user_id: str
    username: str
    display_name: str = ""
    avatar_url: str = ""
    iq_score: int = 0
    knowledge_rank: str = "Novice"
    rank_position: int = 0


# ─── Moderation ────────────────────────────────────────────
class ModerationResult(BaseModel):
    safe: bool
    violations: List[str] = []
    warning_message: str = ""
    strike_count: int = 0


class ViolationResponse(BaseModel):
    id: str
    user_id: str
    violation_type: str
    content_type: str = ""
    severity: str
    created_at: str = ""
