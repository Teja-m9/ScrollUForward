"""
Appwrite Database Setup Script.
Run this once to create all required collections and attributes.
Usage: python setup_db.py
"""
from appwrite.client import Client
from appwrite.services.databases import Databases
from appwrite.id import ID
from config import APPWRITE_ENDPOINT, APPWRITE_PROJECT_ID, APPWRITE_API_KEY, APPWRITE_DATABASE_ID
import time

client = Client()
client.set_endpoint(APPWRITE_ENDPOINT)
client.set_project(APPWRITE_PROJECT_ID)
client.set_key(APPWRITE_API_KEY)
db = Databases(client)


def create_db():
    try:
        db.create(database_id=APPWRITE_DATABASE_ID, name="ScrollUForward DB")
        print(f"[OK] Database '{APPWRITE_DATABASE_ID}' created")
    except Exception as e:
        print(f"[..] Database might already exist: {e}")


def create_collection(collection_id: str, name: str):
    try:
        db.create_collection(
            database_id=APPWRITE_DATABASE_ID,
            collection_id=collection_id,
            name=name,
            document_security=False,
        )
        print(f"  [OK] Collection '{name}' created")
    except Exception as e:
        print(f"  [..] {name}: {e}")


def add_string(col_id, key, size=255, required=False):
    try:
        db.create_string_attribute(APPWRITE_DATABASE_ID, col_id, key, size, required)
    except Exception:
        pass


def add_int(col_id, key, required=False):
    try:
        db.create_integer_attribute(APPWRITE_DATABASE_ID, col_id, key, required)
    except Exception:
        pass


def add_bool(col_id, key, required=False):
    try:
        db.create_boolean_attribute(APPWRITE_DATABASE_ID, col_id, key, required)
    except Exception:
        pass


def add_index(col_id, key, index_type="key", attributes=None):
    try:
        db.create_index(APPWRITE_DATABASE_ID, col_id, key, index_type, attributes or [key])
    except Exception:
        pass


def setup():
    print("[*] Setting up ScrollUForward database...\n")
    create_db()
    time.sleep(1)

    # ─── Users Collection ─────────────────────────────────
    print("\n[+] Creating Users collection...")
    create_collection("users", "Users")
    time.sleep(1)
    add_string("users", "username", 50, True)
    add_string("users", "email", 255, True)
    add_string("users", "password_hash", 255, True)
    add_string("users", "display_name", 100)
    add_string("users", "bio", 500)
    add_string("users", "avatar_url", 500)
    add_int("users", "iq_score")
    add_string("users", "knowledge_rank", 50)
    add_string("users", "interest_tags", 2000)  # JSON string
    add_int("users", "followers_count")
    add_int("users", "following_count")
    add_int("users", "posts_count")
    add_int("users", "streak_days")
    add_string("users", "badges", 2000)  # JSON string
    time.sleep(2)
    add_index("users", "idx_email", "key", ["email"])
    add_index("users", "idx_username", "key", ["username"])
    add_index("users", "idx_iq", "key", ["iq_score"])

    # ─── Content Collection ───────────────────────────────
    print("[+] Creating Content collection...")
    create_collection("content", "Content")
    time.sleep(1)
    add_string("content", "title", 300, True)
    add_string("content", "body", 50000)
    add_string("content", "content_type", 20, True)  # reel, article, news
    add_string("content", "domain", 50, True)
    add_string("content", "author_id", 50)
    add_string("content", "author_username", 50)
    add_string("content", "author_avatar", 500)
    add_string("content", "thumbnail_url", 500)
    add_string("content", "media_url", 500)
    add_string("content", "citations", 5000)  # JSON
    add_string("content", "tags", 2000)  # JSON
    add_int("content", "quality_score")
    add_int("content", "likes_count")
    add_int("content", "saves_count")
    add_int("content", "views_count")
    add_int("content", "comments_count")
    time.sleep(2)
    add_index("content", "idx_type", "key", ["content_type"])
    add_index("content", "idx_domain", "key", ["domain"])
    add_index("content", "idx_author", "key", ["author_id"])

    # ─── Interactions Collection ──────────────────────────
    print("[+] Creating Interactions collection...")
    create_collection("interactions", "Interactions")
    time.sleep(1)
    add_string("interactions", "user_id", 50, True)
    add_string("interactions", "content_id", 50, True)
    add_string("interactions", "interaction_type", 30, True)
    time.sleep(2)
    add_index("interactions", "idx_user", "key", ["user_id"])
    add_index("interactions", "idx_content", "key", ["content_id"])

    # ─── Discussions Collection ───────────────────────────
    print("[+] Creating Discussions collection...")
    create_collection("discussions", "Discussions")
    time.sleep(1)
    add_string("discussions", "title", 300, True)
    add_string("discussions", "description", 5000)
    add_string("discussions", "domain", 50)
    add_string("discussions", "creator_id", 50)
    add_string("discussions", "creator_username", 50)
    add_string("discussions", "creator_avatar", 500)
    add_string("discussions", "tags", 2000)
    add_int("discussions", "comments_count")
    add_int("discussions", "participants_count")
    time.sleep(2)
    add_index("discussions", "idx_domain", "key", ["domain"])

    # ─── Comments Collection ──────────────────────────────
    print("[+] Creating Comments collection...")
    create_collection("comments", "Comments")
    time.sleep(1)
    add_string("comments", "discussion_id", 50, True)
    add_string("comments", "user_id", 50, True)
    add_string("comments", "username", 50)
    add_string("comments", "avatar_url", 500)
    add_string("comments", "body", 5000, True)
    add_string("comments", "citation_url", 500)
    add_int("comments", "likes_count")
    time.sleep(2)
    add_index("comments", "idx_discussion", "key", ["discussion_id"])

    # ─── Content Comments Collection ────────────────────────
    print("[+] Creating Content Comments collection...")
    create_collection("content_comments", "Content Comments")
    time.sleep(1)
    add_string("content_comments", "content_id", 50, True)
    add_string("content_comments", "user_id", 50, True)
    add_string("content_comments", "username", 50)
    add_string("content_comments", "avatar_url", 500)
    add_string("content_comments", "body", 5000, True)
    add_int("content_comments", "likes_count")
    time.sleep(2)
    add_index("content_comments", "idx_content", "key", ["content_id"])


    # ─── Chat Rooms Collection ────────────────────────────
    print("[+] Creating Chat Rooms collection...")
    create_collection("chat_rooms", "Chat Rooms")
    time.sleep(1)
    add_string("chat_rooms", "participants", 5000)  # JSON
    add_bool("chat_rooms", "is_group")
    add_string("chat_rooms", "name", 200)
    add_string("chat_rooms", "last_message", 500)
    add_string("chat_rooms", "last_message_time", 100)
    add_string("chat_rooms", "created_by", 50)

    # ─── Messages Collection ─────────────────────────────
    print("[+] Creating Messages collection...")
    create_collection("messages", "Messages")
    time.sleep(1)
    add_string("messages", "chat_room_id", 50, True)
    add_string("messages", "sender_id", 50, True)
    add_string("messages", "sender_username", 50)
    add_string("messages", "sender_avatar", 500)
    add_string("messages", "body", 5000, True)
    add_string("messages", "message_type", 20)
    add_bool("messages", "is_read")
    time.sleep(2)
    add_index("messages", "idx_room", "key", ["chat_room_id"])
    add_index("messages", "idx_sender", "key", ["sender_id"])

    # ─── User Violations Collection ──────────────────────
    print("[+] Creating User Violations collection...")
    create_collection("user_violations", "User Violations")
    time.sleep(1)
    add_string("user_violations", "user_id", 50, True)
    add_string("user_violations", "violation_type", 50, True)
    add_string("user_violations", "violation_details", 2000)
    add_string("user_violations", "content_type", 20)
    add_string("user_violations", "content_snippet", 500)
    add_string("user_violations", "severity", 20, True)
    add_int("user_violations", "created_at_unix")
    time.sleep(2)
    add_index("user_violations", "idx_user", "key", ["user_id"])
    add_index("user_violations", "idx_severity", "key", ["user_id", "severity"])

    # ─── Add moderation fields to Users ──────────────────
    print("[+] Adding moderation fields to Users...")
    add_int("users", "strike_count")
    add_bool("users", "is_banned")
    add_string("users", "ban_until", 50)

    print("\n[OK] All collections set up successfully!")
    print("[*] Run 'python seed.py' next to add demo data.")


if __name__ == "__main__":
    setup()
