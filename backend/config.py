import os
from dotenv import load_dotenv

load_dotenv()

# ─── Appwrite ──────────────────────────────────────────────
APPWRITE_ENDPOINT = os.getenv("APPWRITE_ENDPOINT", "https://cloud.appwrite.io/v1")
APPWRITE_PROJECT_ID = os.getenv("APPWRITE_PROJECT_ID", "")
APPWRITE_API_KEY = os.getenv("APPWRITE_API_KEY", "")
APPWRITE_DATABASE_ID = os.getenv("APPWRITE_DATABASE_ID", "scrolluforward_db")
JWT_SECRET = os.getenv("JWT_SECRET", "scrolluforward-secret-key-change-me")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 72

# Collection IDs
COLLECTION_USERS = "users"
COLLECTION_CONTENT = "content"
COLLECTION_INTERACTIONS = "interactions"
COLLECTION_DISCUSSIONS = "discussions"
COLLECTION_COMMENTS = "comments"  # Used for discussions
COLLECTION_CONTENT_COMMENTS = "content_comments"
COLLECTION_MESSAGES = "messages"
COLLECTION_CHAT_ROOMS = "chat_rooms"
COLLECTION_USER_VIOLATIONS = "user_violations"

# ─── AI Agent Keys ─────────────────────────────────────────
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GOOGLE_AI_API_KEY = os.getenv("GOOGLE_AI_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY", "")
SERPAPI_KEY = os.getenv("SERPAPI_KEY", "")
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY", "")

# ─── AWS S3 ────────────────────────────────────────────────
AWS_ACCESS_KEY_ID = os.getenv("S3_ACCESS_KEY", os.getenv("AWS_ACCESS_KEY_ID", ""))
AWS_SECRET_ACCESS_KEY = os.getenv("S3_SECRET_KEY", os.getenv("AWS_SECRET_ACCESS_KEY", ""))
AWS_S3_BUCKET = os.getenv("AWS_S3_BUCKET", "scrolluforward-media")
AWS_REGION = os.getenv("S3_REGION", os.getenv("AWS_REGION", "ap-south-1"))
CLOUDFRONT_DOMAIN = os.getenv("CLOUDFRONT_DOMAIN", "cdn.scrolluforward.com")

# ─── Groq Model Config ────────────────────────────────────
GROQ_MODEL_PRIMARY = "llama-3.3-70b-versatile"
GROQ_MODEL_FAST = "llama-3.1-8b-instant"

# ─── IQ Point Values ──────────────────────────────────────
IQ_POINTS = {
    "watch_reel": 5,
    "read_article": 10,
    "complete_quiz": 15,
    "post_discussion": 20,
    "streak_bonus": 50,
    "viral_content": 100,
}

# ─── Content Domains ──────────────────────────────────────
DOMAINS = ["technology", "history", "nature", "physics", "ai",
           "ancient_civilizations", "space", "biology", "chemistry",
           "mathematics", "philosophy", "engineering"]

# Content Types
CONTENT_TYPES = ["reel", "article", "news"]

# ─── News Sources (whitelist) ─────────────────────────────
NEWS_RSS_FEEDS = {
    "Nature": "https://www.nature.com/nature.rss",
    "NASA": "https://www.nasa.gov/rss/dyn/breaking_news.rss",
    "ArXiv_CS": "https://rss.arxiv.org/rss/cs",
    "ArXiv_Physics": "https://rss.arxiv.org/rss/physics",
    "Smithsonian": "https://www.smithsonianmag.com/rss/latest_articles/",
    "BBC_Science": "https://feeds.bbci.co.uk/news/science_and_environment/rss.xml",
    "Scientific_American": "https://rss.sciam.com/ScientificAmerican-Global",
    "PhysOrg": "https://phys.org/rss-feed/",
    "New_Scientist": "https://www.newscientist.com/feed/home/",
    "The_Conversation": "https://theconversation.com/articles.atom",
}

# ─── Validation Thresholds ────────────────────────────────
QUALITY_SCORE_THRESHOLD = 65
BIAS_SCORE_THRESHOLD = 0.3
DUPLICATE_COSINE_THRESHOLD = 0.92

# ─── Content Moderation ──────────────────────────────────
MODERATION_SCORE_THRESHOLD = 0.7   # OpenAI moderation category score to trigger rejection
TEMP_BAN_HOURS = 24
MAX_STRIKES_BEFORE_PERMANENT_BAN = 3
