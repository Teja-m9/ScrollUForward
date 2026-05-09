from appwrite.client import Client
from appwrite.services.databases import Databases
from appwrite.services.users import Users
from appwrite.services.storage import Storage
from appwrite.query import Query
from config import (
    APPWRITE_ENDPOINT, APPWRITE_PROJECT_ID, APPWRITE_API_KEY,
    APPWRITE_DATABASE_ID, COLLECTION_USERS,
)


def get_client() -> Client:
    client = Client()
    client.set_endpoint(APPWRITE_ENDPOINT)
    client.set_project(APPWRITE_PROJECT_ID)
    client.set_key(APPWRITE_API_KEY)
    return client


def get_databases() -> Databases:
    return Databases(get_client())


def get_users_service() -> Users:
    return Users(get_client())


def get_storage() -> Storage:
    return Storage(get_client())


def bulk_get_users(user_ids: list[str]) -> dict[str, dict]:
    """Fetch many user docs in one round-trip per 100 ids.

    Replaces N x get_document loops scattered through brain_routes / user_routes.
    Returns {user_id: doc}, missing entries silently skipped.
    """
    out: dict[str, dict] = {}
    if not user_ids:
        return out
    db = get_databases()
    deduped = list({uid for uid in user_ids if uid})
    for start in range(0, len(deduped), 100):
        chunk = deduped[start:start + 100]
        try:
            res = db.list_documents(
                database_id=APPWRITE_DATABASE_ID,
                collection_id=COLLECTION_USERS,
                queries=[Query.equal("$id", chunk), Query.limit(100)],
            )
            for doc in res.get("documents", []) or []:
                out[doc["$id"]] = doc
        except Exception:
            # If a chunk fails, fall back to single fetches so partial result still works
            for uid in chunk:
                try:
                    out[uid] = db.get_document(
                        database_id=APPWRITE_DATABASE_ID,
                        collection_id=COLLECTION_USERS,
                        document_id=uid,
                    )
                except Exception:
                    continue
    return out
