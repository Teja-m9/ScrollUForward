"""
Strike / Ban System — ScrollUForward
Escalation: 1st → warning, 2nd → 24h ban, 3rd+ → permanent ban.
"""
import json
import logging
import time
from datetime import datetime, timedelta, timezone

from appwrite.query import Query
from appwrite.id import ID
from appwrite_client import get_databases
from config import (
    APPWRITE_DATABASE_ID, COLLECTION_USERS, COLLECTION_USER_VIOLATIONS,
    TEMP_BAN_HOURS, MAX_STRIKES_BEFORE_PERMANENT_BAN,
)

logger = logging.getLogger("strike_system")


async def check_user_ban_status(user_id: str) -> dict:
    """
    Check if a user is banned or temp-suspended.
    Returns {allowed: bool, reason: str, ban_until: str | None}.
    """
    db = get_databases()
    try:
        user = db.get_document(
            database_id=APPWRITE_DATABASE_ID,
            collection_id=COLLECTION_USERS,
            document_id=user_id,
        )

        # Permanent ban
        if user.get("is_banned", False):
            return {
                "allowed": False,
                "reason": "Your account has been permanently suspended due to repeated violations.",
                "ban_until": None,
            }

        # Temporary ban
        ban_until = user.get("ban_until", "")
        if ban_until:
            try:
                ban_dt = datetime.fromisoformat(ban_until.replace("Z", "+00:00"))
                now = datetime.now(timezone.utc)
                if now < ban_dt:
                    remaining = ban_dt - now
                    hours_left = int(remaining.total_seconds() / 3600) + 1
                    return {
                        "allowed": False,
                        "reason": f"Posting suspended for {hours_left} more hour(s) due to content violations.",
                        "ban_until": ban_until,
                    }
                else:
                    # Ban expired — clear it
                    db.update_document(
                        database_id=APPWRITE_DATABASE_ID,
                        collection_id=COLLECTION_USERS,
                        document_id=user_id,
                        data={"ban_until": ""},
                    )
            except (ValueError, TypeError):
                pass

        return {"allowed": True, "reason": "", "ban_until": None}

    except Exception as e:
        logger.error(f"Failed to check ban status for {user_id}: {e}")
        # Fail open — allow if we can't check (don't block on DB errors)
        return {"allowed": True, "reason": "", "ban_until": None}


async def record_violation(
    user_id: str,
    violation_type: str,
    details: dict,
    content_type: str = "",
    snippet: str = "",
) -> dict:
    """
    Record a strike and escalate ban if needed.
    Returns {strike_count: int, action: str, message: str}.
    """
    db = get_databases()

    try:
        # Get current user
        user = db.get_document(
            database_id=APPWRITE_DATABASE_ID,
            collection_id=COLLECTION_USERS,
            document_id=user_id,
        )
        current_strikes = user.get("strike_count", 0) or 0
        new_strikes = current_strikes + 1

        # Determine severity
        if new_strikes >= MAX_STRIKES_BEFORE_PERMANENT_BAN:
            severity = "ban_permanent"
            action = "permanent_ban"
            message = (
                "Your account has been permanently suspended. "
                "You have repeatedly violated our content guidelines."
            )
        elif new_strikes == 2:
            severity = "ban_24h"
            action = "temp_ban"
            message = (
                f"Your posting privileges have been suspended for {TEMP_BAN_HOURS} hours. "
                "This is your second violation. One more will result in a permanent ban."
            )
        else:
            severity = "warning"
            action = "warning"
            message = (
                "Your content was rejected for violating our guidelines. "
                "Repeated violations will result in account suspension."
            )

        # Record the violation
        db.create_document(
            database_id=APPWRITE_DATABASE_ID,
            collection_id=COLLECTION_USER_VIOLATIONS,
            document_id=ID.unique(),
            data={
                "user_id": user_id,
                "violation_type": violation_type,
                "violation_details": json.dumps(details)[:2000],
                "content_type": content_type,
                "content_snippet": snippet[:500],
                "severity": severity,
                "created_at_unix": int(time.time()),
            },
        )

        # Update user record
        update_data = {"strike_count": new_strikes}
        if action == "permanent_ban":
            update_data["is_banned"] = True
        elif action == "temp_ban":
            ban_until = (
                datetime.now(timezone.utc) + timedelta(hours=TEMP_BAN_HOURS)
            ).isoformat()
            update_data["ban_until"] = ban_until

        db.update_document(
            database_id=APPWRITE_DATABASE_ID,
            collection_id=COLLECTION_USERS,
            document_id=user_id,
            data=update_data,
        )

        logger.warning(
            f"[Strike] user={user_id} strike={new_strikes} action={action} type={violation_type}"
        )

        return {
            "strike_count": new_strikes,
            "action": action,
            "message": message,
        }

    except Exception as e:
        logger.error(f"Failed to record violation for {user_id}: {e}")
        return {
            "strike_count": 0,
            "action": "error",
            "message": "Content rejected for safety reasons.",
        }


async def get_user_violations(user_id: str) -> list:
    """Get violation history for a user."""
    db = get_databases()
    try:
        result = db.list_documents(
            database_id=APPWRITE_DATABASE_ID,
            collection_id=COLLECTION_USER_VIOLATIONS,
            queries=[
                Query.equal("user_id", user_id),
                Query.order_desc("$createdAt"),
                Query.limit(50),
            ],
        )
        return [
            {
                "id": doc["$id"],
                "violation_type": doc.get("violation_type", ""),
                "content_type": doc.get("content_type", ""),
                "severity": doc.get("severity", ""),
                "content_snippet": doc.get("content_snippet", ""),
                "created_at": doc.get("$createdAt", ""),
            }
            for doc in result["documents"]
        ]
    except Exception as e:
        logger.error(f"Failed to fetch violations for {user_id}: {e}")
        return []
