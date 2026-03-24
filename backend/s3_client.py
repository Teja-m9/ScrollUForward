"""
AWS S3 client — uploads media to scrolluforward-media bucket.
All binary files (MP4, images) live in S3, never in Appwrite.
Uses presigned URLs (24h expiry) for access since no CloudFront yet.
"""
import boto3
from datetime import datetime
from config import (
    AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY,
    AWS_S3_BUCKET, AWS_REGION,
)

PRESIGN_EXPIRY = 86400  # 24 hours


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


def upload_reel(local_path: str, domain: str, reel_id: str) -> str:
    """Upload reel MP4 → s3://scrolluforward-media/reels/{domain}/{date}/{reel_id}.mp4"""
    s3 = get_s3_client()
    key = f"reels/{domain}/{_today()}/{reel_id}.mp4"
    s3.upload_file(
        local_path, AWS_S3_BUCKET, key,
        ExtraArgs={"ContentType": "video/mp4"},
    )
    return _presigned_url(key)


def upload_thumbnail(image_bytes: bytes, domain: str, item_id: str, suffix: str = "thumb") -> str:
    """Upload image bytes → s3://scrolluforward-media/reels/{domain}/{date}/{id}_thumb.jpg"""
    s3 = get_s3_client()
    key = f"reels/{domain}/{_today()}/{item_id}_{suffix}.jpg"
    s3.put_object(
        Bucket=AWS_S3_BUCKET, Key=key, Body=image_bytes,
        ContentType="image/jpeg",
    )
    return _presigned_url(key)


def upload_blog_cover(image_bytes: bytes, domain: str, blog_id: str) -> str:
    """Upload blog cover image → s3://scrolluforward-media/blogs/{domain}/{date}/{id}_cover.jpg"""
    s3 = get_s3_client()
    key = f"blogs/{domain}/{_today()}/{blog_id}_cover.jpg"
    s3.put_object(
        Bucket=AWS_S3_BUCKET, Key=key, Body=image_bytes,
        ContentType="image/jpeg",
    )
    return _presigned_url(key)


def upload_audio(local_path: str, domain: str, reel_id: str) -> str:
    """Upload TTS audio → s3://scrolluforward-media/reels/{domain}/{date}/{id}_audio.mp3"""
    s3 = get_s3_client()
    key = f"reels/{domain}/{_today()}/{reel_id}_audio.mp3"
    s3.upload_file(
        local_path, AWS_S3_BUCKET, key,
        ExtraArgs={"ContentType": "audio/mpeg"},
    )
    return _presigned_url(key)


def upload_news_image(image_bytes: bytes, domain: str, news_id: str) -> str:
    """Upload news hero image → s3://scrolluforward-media/news/{domain}/{date}/{id}_img.jpg"""
    s3 = get_s3_client()
    key = f"news/{domain}/{_today()}/{news_id}_img.jpg"
    s3.put_object(
        Bucket=AWS_S3_BUCKET, Key=key, Body=image_bytes,
        ContentType="image/jpeg",
    )
    return _presigned_url(key)
