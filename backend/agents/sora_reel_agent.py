"""
Sora-based reel agent — OpenAI Sora-2 video generation.

Pipeline:
  Groq (scene plan) → Sora-2 (AI video clips, 720x1280 portrait) →
  FFmpeg (concat + upscale) → Deepgram TTS → FFmpeg (merge audio) →
  S3 → Appwrite
"""
import asyncio
import json
import logging
import os
import subprocess
import tempfile
import time

import httpx

log = logging.getLogger("sora_reel_agent")

FFMPEG = r"C:\KMPlayer\ffmpeg.exe"
SORA_MODEL = "sora-2"
SORA_SIZE  = "720x1280"   # portrait — perfect for vertical reels
SORA_SECS  = 8            # 4, 8, or 12 (Sora supported values)


# ── 1. Scene planning ─────────────────────────────────────────────────────────

async def plan_scenes(topic: str, narration: str) -> list:
    """Use Groq to produce 5 scene descriptions + Sora video prompts."""
    from groq import AsyncGroq
    groq = AsyncGroq(api_key=os.environ["GROQ_API_KEY"])

    system = """You are a video director for an educational animation series.
Break the narration into exactly 5 scenes. For each scene output a JSON object with:
- "scene_number": int (1-5)
- "narration_chunk": verbatim slice of the narration
- "sora_prompt": a vivid, concrete video prompt for an AI video model.
  The prompt must describe MOTION (what is moving, how), not just a still image.
  Style: flat 2D animated illustration, bright vivid colors, dark navy blue (#0a0e1f) background,
  cute round-faced cartoon characters, smooth flowing motion, educational infographic animation.
  NO text overlays in the video. Keep prompts under 200 words.
  Do NOT reference any real YouTube channels or brand names.

Return a raw JSON array ONLY — no markdown, no explanation."""

    resp = await groq.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": f"Topic: {topic}\n\nNarration:\n{narration}"},
        ],
        temperature=0.7,
        max_tokens=2000,
    )
    text = resp.choices[0].message.content.strip()
    start = text.find("[")
    end   = text.rfind("]") + 1
    if start == -1 or end == 0:
        raise ValueError(f"No JSON array in Groq response:\n{text[:300]}")
    return json.loads(text[start:end])


# ── 2. Submit + poll Sora jobs ────────────────────────────────────────────────

def submit_sora_job(client, prompt: str) -> str:
    """Submit a Sora video job and return the job ID."""
    job = client.videos.create(
        model=SORA_MODEL,
        prompt=prompt,
        size=SORA_SIZE,
        seconds=SORA_SECS,
    )
    log.info(f"  Sora job submitted: {job.id[:30]}... status={job.status}")
    return job.id


def poll_sora_job(client, job_id: str, timeout: int = 600) -> str | None:
    """Poll until complete. Returns download URL or None on failure."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        v = client.videos.retrieve(job_id)
        log.info(f"  {job_id[:20]}... status={v.status} progress={v.progress}%")
        if v.status == "completed":
            # Download the video content
            return job_id   # We'll download separately using download_content
        if v.status in ("failed", "cancelled"):
            log.error(f"  Sora job failed: {getattr(v, 'error', v.status)}")
            return None
        time.sleep(15)
    log.error(f"  Sora job timed out: {job_id}")
    return None


def download_sora_video(client, job_id: str, output_path: str) -> bool:
    """Download completed Sora video to file."""
    try:
        response = client.videos.download_content(job_id)
        # HttpxBinaryResponseContent — .content gives raw bytes directly
        with open(output_path, "wb") as f:
            f.write(response.content)
        log.info(f"  Downloaded: {os.path.getsize(output_path) // 1024} KB → {output_path}")
        return True
    except Exception as e:
        log.error(f"  Download failed for {job_id}: {e}")
        return False


# ── 3. FFmpeg utilities ───────────────────────────────────────────────────────

def concat_clips(clip_paths: list, output_path: str) -> bool:
    list_file = output_path + "_list.txt"
    with open(list_file, "w") as f:
        for p in clip_paths:
            f.write(f"file '{p}'\n")

    cmd = [FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", list_file, "-c", "copy", output_path]
    res = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if res.returncode != 0:
        log.error(f"  concat failed: {res.stderr[-400:]}")
        return False
    return True


def upscale_and_merge(video_path: str, audio_path: str, output_path: str, has_audio: bool) -> bool:
    """Upscale 720x1280 → 1080x1920 and optionally merge audio."""
    if has_audio:
        cmd = [
            FFMPEG, "-y",
            "-i", video_path,
            "-i", audio_path,
            "-map", "0:v:0", "-map", "1:a:0",
            "-vf", "scale=1080:1920:flags=lanczos",
            "-c:v", "libx264", "-preset", "fast", "-crf", "20",
            "-strict", "-2", "-c:a", "aac", "-shortest",
            output_path,
        ]
    else:
        cmd = [
            FFMPEG, "-y",
            "-i", video_path,
            "-vf", "scale=1080:1920:flags=lanczos",
            "-c:v", "libx264", "-preset", "fast", "-crf", "20",
            output_path,
        ]
    res = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if res.returncode != 0:
        log.error(f"  upscale/merge failed: {res.stderr[-400:]}")
        return False
    return True


# ── Main pipeline ─────────────────────────────────────────────────────────────

async def generate_sora_reel(
    topic: str,
    domain: str,
    narration: str,
    reel_id: str,
) -> dict:
    """Full Sora-based reel pipeline."""
    from openai import OpenAI
    from agents.reel_agent import generate_voiceover, extract_thumbnail
    from agents.domain_router import publish_reel
    from s3_client import upload_reel, upload_thumbnail

    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    tmp = tempfile.mkdtemp(prefix=f"sorareel_{domain}_")
    log.info(f"Temp dir: {tmp}")

    # 1 — Plan scenes
    log.info("Planning scenes with Groq...")
    scenes = await plan_scenes(topic, narration)
    log.info(f"Got {len(scenes)} scenes")

    # 2 — Submit all Sora jobs (can run in parallel — they're async server-side)
    log.info("Submitting Sora video jobs...")
    job_ids = []
    for i, scene in enumerate(scenes):
        try:
            jid = submit_sora_job(client, scene["sora_prompt"])
            job_ids.append((i, jid, scene))
        except Exception as e:
            log.error(f"  Scene {i+1} submit failed: {e}")
            job_ids.append((i, None, scene))

    # 3 — Poll all jobs until done
    log.info("Polling Sora jobs (this takes a few minutes)...")
    clip_paths = []
    for i, job_id, scene in job_ids:
        if job_id is None:
            continue
        log.info(f"  Waiting for scene {i+1}...")
        completed = poll_sora_job(client, job_id, timeout=600)
        if completed:
            clip_path = os.path.join(tmp, f"clip_{i:02d}.mp4")
            if download_sora_video(client, job_id, clip_path):
                clip_paths.append(clip_path)
            else:
                log.warning(f"  Scene {i+1} download failed")
        else:
            log.warning(f"  Scene {i+1} generation failed")

    if not clip_paths:
        return {"status": "error", "error": "No Sora clips generated"}

    log.info(f"{len(clip_paths)}/{len(scenes)} clips ready")

    # 4 — Concatenate clips
    concat_path = os.path.join(tmp, "concat.mp4")
    log.info("Concatenating clips...")
    if not concat_clips(clip_paths, concat_path):
        return {"status": "error", "error": "Concat failed"}

    # 5 — TTS narration
    log.info("Generating TTS narration...")
    audio_path = os.path.join(tmp, "narration.mp3")
    await generate_voiceover(narration.strip(), audio_path)
    has_audio = os.path.exists(audio_path) and os.path.getsize(audio_path) > 0
    if has_audio:
        log.info(f"TTS: {os.path.getsize(audio_path) // 1024} KB")
    else:
        log.warning("TTS failed — proceeding muted")

    # 6 — Upscale + merge audio
    final_path = os.path.join(tmp, f"{reel_id}.mp4")
    log.info("Upscaling to 1080x1920 and merging audio...")
    if not upscale_and_merge(concat_path, audio_path, final_path, has_audio):
        final_path = concat_path
    log.info(f"Final: {os.path.getsize(final_path) // 1024} KB")

    # 7 — S3 upload
    log.info("Uploading to S3...")
    s3_video_url = upload_reel(final_path, domain, reel_id)
    log.info(f"S3: {s3_video_url[:70]}...")

    s3_thumb_url = ""
    thumb_path = os.path.join(tmp, f"{reel_id}_thumb.jpg")
    if extract_thumbnail(final_path, thumb_path):
        with open(thumb_path, "rb") as f:
            s3_thumb_url = upload_thumbnail(f.read(), domain, reel_id)
        log.info("Thumbnail uploaded")

    # 8 — Publish Appwrite
    log.info("Publishing to Appwrite...")
    result = publish_reel({
        "reel_id": reel_id,
        "domain": domain,
        "title": topic,
        "script_text": narration.strip(),
        "s3_video_url": s3_video_url,
        "s3_thumb_url": s3_thumb_url,
        "source_type": "ai_generated",
        "content_type": "reel",
        "quality_score": 95,
    })

    return {
        **result,
        "s3_video_url": s3_video_url,
        "s3_thumb_url": s3_thumb_url,
        "has_audio": has_audio,
        "clips_count": len(clip_paths),
    }
