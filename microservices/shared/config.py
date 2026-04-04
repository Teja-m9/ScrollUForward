"""Shared configuration for all microservices."""
import os
from dotenv import load_dotenv

load_dotenv()

# ── Appwrite ──────────────────────────────────────────
APPWRITE_ENDPOINT    = os.getenv("APPWRITE_ENDPOINT", "https://cloud.appwrite.io/v1")
APPWRITE_PROJECT_ID  = os.getenv("APPWRITE_PROJECT_ID", "")
APPWRITE_API_KEY     = os.getenv("APPWRITE_API_KEY", "")
APPWRITE_DATABASE_ID = os.getenv("APPWRITE_DATABASE_ID", "scrolluforward_db")

# ── Collections ───────────────────────────────────────
COLLECTION_USERS          = "users"
COLLECTION_CONTENT        = "content"
COLLECTION_INTERACTIONS   = "interactions"
COLLECTION_DISCUSSIONS    = "discussions"
COLLECTION_COMMENTS       = "comments"
COLLECTION_CONTENT_COMMENTS = "content_comments"
COLLECTION_MESSAGES       = "messages"
COLLECTION_CHAT_ROOMS     = "chat_rooms"
COLLECTION_USER_VIOLATIONS = "user_violations"

# ── JWT ───────────────────────────────────────────────
JWT_SECRET           = os.getenv("JWT_SECRET", "scrolluforward-secret-change-me")
JWT_ALGORITHM        = "HS256"
JWT_EXPIRATION_HOURS = 72

# ── AWS S3 ────────────────────────────────────────────
AWS_ACCESS_KEY_ID     = os.getenv("S3_ACCESS_KEY", os.getenv("AWS_ACCESS_KEY_ID", ""))
AWS_SECRET_ACCESS_KEY = os.getenv("S3_SECRET_KEY", os.getenv("AWS_SECRET_ACCESS_KEY", ""))
AWS_S3_BUCKET         = os.getenv("AWS_S3_BUCKET", "scrolluforward-media")
AWS_REGION            = os.getenv("S3_REGION", "ap-south-1")

# ── AI Keys ───────────────────────────────────────────
GROQ_API_KEY      = os.getenv("GROQ_API_KEY", "")
GOOGLE_AI_API_KEY = os.getenv("GOOGLE_AI_API_KEY", "")
OPENAI_API_KEY    = os.getenv("OPENAI_API_KEY", "")
DEEPGRAM_API_KEY  = os.getenv("DEEPGRAM_API_KEY", "")
NEWSAPI_KEY       = os.getenv("NEWSAPI_KEY", "")

# ── Redis ─────────────────────────────────────────────
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# ── Service URLs (internal) ───────────────────────────
AUTH_SERVICE_URL       = os.getenv("AUTH_SERVICE_URL",       "http://auth:8001")
CONTENT_SERVICE_URL    = os.getenv("CONTENT_SERVICE_URL",    "http://content:8002")
DISCUSSION_SERVICE_URL = os.getenv("DISCUSSION_SERVICE_URL", "http://discussion:8003")
USER_SERVICE_URL       = os.getenv("USER_SERVICE_URL",       "http://user:8004")
CHAT_SERVICE_URL       = os.getenv("CHAT_SERVICE_URL",       "http://chat:8005")
AI_WORKER_SERVICE_URL  = os.getenv("AI_WORKER_SERVICE_URL",  "http://ai_worker:8006")

# ── Groq Models ───────────────────────────────────────
GROQ_MODEL_PRIMARY = "llama-3.3-70b-versatile"
GROQ_MODEL_FAST    = "llama-3.1-8b-instant"

# ── Domains ───────────────────────────────────────────
DOMAINS = ["technology", "history", "nature", "physics", "ai",
           "ancient_civilizations", "space", "biology", "chemistry",
           "mathematics", "philosophy", "engineering"]

QUALITY_SCORE_THRESHOLD = 65
TEMP_BAN_HOURS = 24
MAX_STRIKES_BEFORE_PERMANENT_BAN = 3

# ── Rate Limits ───────────────────────────────────────
RATE_LIMIT_DEFAULT  = "100/minute"
RATE_LIMIT_AUTH     = "20/minute"
RATE_LIMIT_AI_CHAT  = "30/minute"
RATE_LIMIT_PIPELINE = "5/minute"
