"""
AWS S3 client — uploads media to scrolluforward-media bucket.
All binary files (MP4, images) live in S3, never in Appwrite.

Stage 2 (CDN): when MEDIA_CDN_DOMAIN is set, public uploads (reels, news,
blogs, audio) are stored with public-read ACL + immutable Cache-Control and
returned as CDN URLs. Chat attachments stay private (presigned, 24 h).
"""
import boto3
from datetime import datetime
from config import (
    AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY,
    AWS_S3_BUCKET, AWS_REGION,
    MEDIA_CDN_DOMAIN, USE_CDN,
)

PRESIGN_EXPIRY = 86400  # 24 hours

# Cache-Control for content-addressed (immutable) public objects
PUBLIC_CACHE_CONTROL = "public, max-age=31536000, immutable"


def get_s3_client():
    return boto3.client(
        "s3",
        region_name=AWS_REGION,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        endpoint_url=f"https://s3.{AWS_REGION}.amazonaws.com",
    )


def _today() -> str:
    return datetime.utcnow().strftime("%Y-%m-%d")


def _presigned_url(key: str) -> str:
    """Generate a presigned URL for the given S3 key."""
    s3 = get_s3_client()
    return s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": AWS_S3_BUCKET, "Key": key},
        ExpiresIn=PRESIGN_EXPIRY,
    )


def _cdn_url(key: str) -> str:
    """Public CDN URL for an object — used when MEDIA_CDN_DOMAIN is configured."""
    return f"https://{MEDIA_CDN_DOMAIN}/{key.lstrip('/')}"


def _public_url(key: str) -> str:
    """Pick CDN URL when CDN is wired, otherwise fall back to presigned."""
    return _cdn_url(key) if USE_CDN else _presigned_url(key)


def _public_extra_args(content_type: str) -> dict:
    """ExtraArgs / put_object kwargs for objects that should be served via CDN."""
    extra = {"ContentType": content_type, "CacheControl": PUBLIC_CACHE_CONTROL}
    if USE_CDN:
        # Only flip ACL public when the bucket's policy permits it (CDN flow)
        extra["ACL"] = "public-read"
    return extra


def upload_reel(local_path: str, domain: str, reel_id: str) -> str:
    """Upload reel MP4 → s3://scrolluforward-media/reels/{domain}/{date}/{reel_id}.mp4"""
    s3 = get_s3_client()
    key = f"reels/{domain}/{_today()}/{reel_id}.mp4"
    s3.upload_file(
        local_path, AWS_S3_BUCKET, key,
        ExtraArgs=_public_extra_args("video/mp4"),
    )
    return _public_url(key)


def upload_thumbnail(image_bytes: bytes, domain: str, item_id: str, suffix: str = "thumb") -> str:
    """Upload image bytes → s3://scrolluforward-media/reels/{domain}/{date}/{id}_thumb.jpg"""
    s3 = get_s3_client()
    key = f"reels/{domain}/{_today()}/{item_id}_{suffix}.jpg"
    s3.put_object(
        Bucket=AWS_S3_BUCKET, Key=key, Body=image_bytes,
        **_public_extra_args("image/jpeg"),
    )
    return _public_url(key)


def upload_blog_cover(image_bytes: bytes, domain: str, blog_id: str) -> str:
    """Upload blog cover image → s3://scrolluforward-media/blogs/{domain}/{date}/{id}_cover.jpg"""
    s3 = get_s3_client()
    key = f"blogs/{domain}/{_today()}/{blog_id}_cover.jpg"
    s3.put_object(
        Bucket=AWS_S3_BUCKET, Key=key, Body=image_bytes,
        **_public_extra_args("image/jpeg"),
    )
    return _public_url(key)


def upload_audio(local_path: str, domain: str, reel_id: str) -> str:
    """Upload TTS audio → s3://scrolluforward-media/reels/{domain}/{date}/{id}_audio.mp3"""
    s3 = get_s3_client()
    key = f"reels/{domain}/{_today()}/{reel_id}_audio.mp3"
    s3.upload_file(
        local_path, AWS_S3_BUCKET, key,
        ExtraArgs=_public_extra_args("audio/mpeg"),
    )
    return _public_url(key)


def upload_news_image(image_bytes: bytes, domain: str, news_id: str) -> str:
    """Upload news hero image → s3://scrolluforward-media/news/{domain}/{date}/{id}_img.jpg"""
    s3 = get_s3_client()
    key = f"news/{domain}/{_today()}/{news_id}_img.jpg"
    s3.put_object(
        Bucket=AWS_S3_BUCKET, Key=key, Body=image_bytes,
        **_public_extra_args("image/jpeg"),
    )
    return _public_url(key)


def upload_chat_attachment(file_bytes: bytes, user_id: str, ext: str = "jpg",
                            content_type: str = "image/jpeg") -> str:
    """Upload a chat-message attachment to S3. Always presigned (private). Path:
        chat/{user_id}/{date}/{timestamp}.{ext}
    """
    import time, uuid
    s3 = get_s3_client()
    ts = int(time.time() * 1000)
    rand = uuid.uuid4().hex[:6]
    key = f"chat/{user_id}/{_today()}/{ts}_{rand}.{ext}"
    s3.put_object(
        Bucket=AWS_S3_BUCKET, Key=key, Body=file_bytes,
        ContentType=content_type,
    )
    # Always presigned — DM media is private
    return _presigned_url(key)
