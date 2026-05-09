# Appwrite Indexes — Stage 3 of the 10k+ MAU scale-out

Appwrite Cloud is a managed BaaS, so we can't run `CREATE INDEX` statements
directly — every index is configured in the Appwrite Console under
**Database → Collections → \<Name\> → Indexes**, OR via the `appwrite` CLI.

Apply the indexes below before traffic exceeds ~1k DAU. Without them, queries
that scan the full collection will get exponentially slower as data grows.

---

## How to apply

### Option A — Appwrite Console (manual)

1. Open https://cloud.appwrite.io/console.
2. Select project `scrolluforward`.
3. **Databases → scrolluforward_db → \<Collection\>**.
4. Tab **Indexes** → **Create Index** → fill the fields below.
5. Wait for status `available` (a few seconds for empty collections; minutes
   for 10k+ rows).

### Option B — Appwrite CLI (scriptable)

```bash
appwrite databases createIndex \
  --databaseId scrolluforward_db \
  --collectionId interactions \
  --key idx_user_id \
  --type key \
  --attributes user_id
```

Repeat per row in the table below.

---

## Required indexes

### `interactions`

| key | type | attributes | order | reason |
|---|---|---|---|---|
| `idx_user_id` | key | `user_id` | ASC | every per-user query (brain map, stats, feed) |
| `idx_content_id` | key | `content_id` | ASC | content interaction counts |
| `idx_interaction_type` | key | `interaction_type` | ASC | `follow` / `like` / `view` filters |
| `idx_created_at` | key | `$createdAt` | DESC | trending cutoff queries |
| `idx_user_created` | key | `user_id`, `$createdAt` | ASC, DESC | user's recent activity (streaks, daily-goal) |
| `idx_follow_lookup` | key | `interaction_type`, `content_id`, `user_id` | ASC, ASC, ASC | followers/following list |

### `content`

| key | type | attributes | order | reason |
|---|---|---|---|---|
| `idx_author_id` | key | `author_id` | ASC | user's posts grid |
| `idx_domain` | key | `domain` | ASC | feed filtering by domain |
| `idx_content_type` | key | `content_type` | ASC | reels / articles / news / story split |
| `idx_created_at` | key | `$createdAt` | DESC | recent posts |
| `idx_type_created` | key | `content_type`, `$createdAt` | ASC, DESC | "latest reels", "latest news" pages |

### `messages`

| key | type | attributes | order | reason |
|---|---|---|---|---|
| `idx_room_created` | key | `chat_room_id`, `$createdAt` | ASC, DESC | message timeline per room |

### `chat_rooms`

| key | type | attributes | order | reason |
|---|---|---|---|---|
| `idx_participants` | key | `participants` | ASC | resolve a user's rooms |

### `comments` (used for discussion comments)

| key | type | attributes | order | reason |
|---|---|---|---|---|
| `idx_discussion_id` | key | `discussion_id` | ASC | discussion thread |

### `content_comments`

| key | type | attributes | order | reason |
|---|---|---|---|---|
| `idx_content_id` | key | `content_id` | ASC | reel/article comment loads |

### `users`

| key | type | attributes | order | reason |
|---|---|---|---|---|
| `idx_username_unique` | unique | `username` | ASC | enforce username uniqueness + lookups |
| `idx_email_unique` | unique | `email` | ASC | login lookup |
| `idx_iq_score` | key | `iq_score` | DESC | leaderboard |

---

## Verification

After applying, hit the verify script in `acceptance.sh` (Stage 5):

```bash
appwrite databases listIndexes --databaseId scrolluforward_db --collectionId interactions
appwrite databases listIndexes --databaseId scrolluforward_db --collectionId content
# ... repeat
```

Every row should show `status: available`.

If any show `processing`, wait — Appwrite is still building. If any show
`failed`, paste the error here and we'll redesign that index (most often a
non-string field used as `unique` against a key with empty values).

---

## Related code-side caps

`backend/schemas.py` declares `MAX_PAGE = 100`. Every paginated endpoint's
`limit` parameter has `Query(le=MAX_PAGE, ge=1)` so callers can't request
unbounded result sets. The `/map/trending` endpoint already reads from a
60-second Redis cache (see `cache.py`); its underlying scan is capped at
2 000 in `map_routes.py:152` and will be moved to a 60-second background
worker refresh in Stage 4 (`worker.py: refresh_trending_aggregate`).
