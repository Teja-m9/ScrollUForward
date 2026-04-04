"""
Remove reels with no video (empty media_url) from Appwrite.
Run: python cleanup_empty_reels.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from appwrite_client import get_databases
from appwrite.query import Query
from config import APPWRITE_DATABASE_ID, COLLECTION_CONTENT

def cleanup():
    db = get_databases()
    deleted = 0
    offset = 0

    while True:
        result = db.list_documents(
            database_id=APPWRITE_DATABASE_ID,
            collection_id=COLLECTION_CONTENT,
            queries=[
                Query.equal("content_type", "reel"),
                Query.equal("media_url", ""),
                Query.limit(100),
                Query.offset(offset),
            ],
        )
        docs = result["documents"]
        if not docs:
            break

        for doc in docs:
            try:
                db.delete_document(
                    database_id=APPWRITE_DATABASE_ID,
                    collection_id=COLLECTION_CONTENT,
                    document_id=doc["$id"],
                )
                print(f"  Deleted: {doc['$id']} — {doc.get('title', '(no title)')}")
                deleted += 1
            except Exception as e:
                print(f"  Failed to delete {doc['$id']}: {e}")

        if len(docs) < 100:
            break
        offset += 100

    print(f"\nDone. Deleted {deleted} empty reels.")

if __name__ == "__main__":
    cleanup()
