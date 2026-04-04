"""
Image-based reel agent — Kurzgesagt-style illustrated video.

Pipeline:
  Groq (scene plan) → DALL-E 3 (flat art images) →
  FFmpeg zoompan (Ken Burns animation) → Deepgram TTS →
  FFmpeg (merge) → S3 → Appwrite
"""
import asyncio
import json
import logging
import os
import subprocess
import tempfile

import httpx

log = logging.getLogger("image_reel_agent")

KURZGESAGT_STYLE = (
    "flat 2D vector illustration art, inspired by Kurzgesagt educational YouTube channel style, "
    "dark navy blue background (#0a0e1f), bright vivid accent colors, clean bold geometric shapes, "
    "cute expressive round-faced characters, colorful icons and infographic elements, "
    "NO text or labels in the image, smooth thick outlines, warm glow lighting accents, "
    "high quality digital art, vertical 9:16 portrait composition, centered focal point"
)

FFMPEG = r"C:\KMPlayer\ffmpeg.exe"


# ── 1. Scene planning ─────────────────────────────────────────────────────────

async def generate_scene_plan(topic: str, narration: str) -> list:
    """Use Groq to split narration into 5-6 scenes with DALL-E prompts."""
    from groq import AsyncGroq

    groq = AsyncGroq(api_key=os.environ["GROQ_API_KEY"])

    system = """You are a visual director for an educational YouTube channel (Kurzgesagt style).
Split the narration into exactly 5 scenes.
For each scene return a JSON object with:
- "scene_number": integer (1-5)
- "narration_chunk": the verbatim portion of narration for this scene
- "visual_description": a vivid description of what to illustrate (flat art style, no copyrighted characters, original cute geometric characters only)
- "duration_hint": approximate seconds (6-12)

Return a JSON array ONLY. No markdown, no explanation."""

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
    end = text.rfind("]") + 1
    if start == -1 or end == 0:
        raise ValueError(f"Groq did not return JSON array:\n{text[:300]}")
    return json.loads(text[start:end])


# ── 2. DALL-E image generation ────────────────────────────────────────────────

async def generate_scene_image(visual_description: str, scene_num: int, output_path: str) -> bool:
    """Generate a single scene illustration with DALL-E 3."""
    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=os.environ["OPENAI_API_KEY"])
    prompt = f"{KURZGESAGT_STYLE}. Scene concept: {visual_description}"

    try:
        resp = await client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1792",   # portrait — closest to 9:16
            quality="standard",
            n=1,
        )
        image_url = resp.data[0].url
        async with httpx.AsyncClient(timeout=90) as hclient:
            r = await hclient.get(image_url)
            r.raise_for_status()
            with open(output_path, "wb") as f:
                f.write(r.content)
        log.info(f"  Scene {scene_num} image: {os.path.getsize(output_path) // 1024} KB")
        return True
    except Exception as e:
        log.error(f"  DALL-E scene {scene_num} failed: {e}")
        return False


# ── 3. Animate still image → video clip (Ken Burns / zoompan) ────────────────

def animate_image_clip(image_path: str, output_path: str, duration: float = 8.0) -> bool:
    """Animate a still PNG into a smooth zoompan video clip."""
    frames = int(duration * 30)

    # Old KMPlayer FFmpeg (2015) does NOT support fps= inside zoompan.
    # Use -framerate at input + -r at output instead.
    zoom_filter = (
        f"zoompan=z='min(zoom+0.0006,1.20)':d={frames}:"
        f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920,"
        f"scale=1080:1920,"
        f"format=yuv420p"
    )

    cmd = [
        FFMPEG, "-y",
        "-loop", "1",
        "-framerate", "30",   # input framerate hint (old FFmpeg needs this)
        "-i", image_path,
        "-vf", zoom_filter,
        "-t", str(duration),
        "-r", "30",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "22",
        output_path,
    ]

    res = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    if res.returncode != 0:
        log.error(f"  zoompan failed:\n{res.stderr[-500:]}")
        return False
    log.info(f"  Clip {output_path}: {os.path.getsize(output_path) // 1024} KB")
    return True


# ── 4. Concatenate clips ──────────────────────────────────────────────────────

def concat_clips(clip_paths: list, output_path: str) -> bool:
    list_file = output_path + "_list.txt"
    with open(list_file, "w") as f:
        for p in clip_paths:
            f.write(f"file '{p}'\n")

    cmd = [
        FFMPEG, "-y",
        "-f", "concat", "-safe", "0",
        "-i", list_file,
        "-c", "copy",
        output_path,
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if res.returncode != 0:
        log.error(f"  concat failed:\n{res.stderr[-400:]}")
        return False
    return True


# ── 5. Merge video + audio ────────────────────────────────────────────────────

def merge_audio(video_path: str, audio_path: str, output_path: str) -> bool:
    cmd = [
        FFMPEG, "-y",
        "-i", video_path,
        "-i", audio_path,
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-c:v", "copy",
        "-strict", "-2",
        "-c:a", "aac",
        "-shortest",
        output_path,
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if res.returncode != 0:
        log.error(f"  audio merge failed:\n{res.stderr[-400:]}")
        return False
    return True


# ── Main pipeline ─────────────────────────────────────────────────────────────

async def generate_image_reel(
    topic: str,
    domain: str,
    narration: str,
    reel_id: str,
) -> dict:
    """Full Kurzgesagt-style image reel pipeline."""
    from agents.reel_agent import generate_voiceover, extract_thumbnail
    from agents.domain_router import publish_reel
    from s3_client import upload_reel, upload_thumbnail

    tmp = tempfile.mkdtemp(prefix=f"imgreel_{domain}_")
    log.info(f"Temp dir: {tmp}")

    # 1 — Scene plan
    log.info("Planning scenes...")
    scenes = await generate_scene_plan(topic, narration)
    log.info(f"Got {len(scenes)} scenes")

    # 2 — Generate images (parallel)
    log.info("Generating DALL-E 3 illustrations...")
    img_paths = [os.path.join(tmp, f"scene_{i:02d}.png") for i in range(len(scenes))]
    img_results = await asyncio.gather(*[
        generate_scene_image(scene["visual_description"], i + 1, img_paths[i])
        for i, scene in enumerate(scenes)
    ])

    # 3 — Animate clips (sequential — CPU bound)
    log.info("Animating clips...")
    clip_paths = []
    for i, (scene, img_path, ok) in enumerate(zip(scenes, img_paths, img_results)):
        if not ok or not os.path.exists(img_path):
            log.warning(f"  Scene {i+1} skipped (no image)")
            continue
        duration = float(scene.get("duration_hint", 8))
        clip_path = os.path.join(tmp, f"clip_{i:02d}.mp4")
        if animate_image_clip(img_path, clip_path, duration):
            clip_paths.append(clip_path)

    if not clip_paths:
        return {"status": "error", "error": "No clips generated"}

    # 4 — Concatenate
    log.info(f"Concatenating {len(clip_paths)} clips...")
    concat_path = os.path.join(tmp, "concat_raw.mp4")
    if not concat_clips(clip_paths, concat_path):
        return {"status": "error", "error": "Concat failed"}

    # 5 — TTS
    log.info("Generating TTS narration...")
    audio_path = os.path.join(tmp, "narration.mp3")
    await generate_voiceover(narration.strip(), audio_path)
    has_audio = os.path.exists(audio_path) and os.path.getsize(audio_path) > 0
    if has_audio:
        log.info(f"TTS: {os.path.getsize(audio_path) // 1024} KB")
    else:
        log.warning("TTS failed — proceeding without audio")

    # 6 — Merge
    final_path = os.path.join(tmp, f"{reel_id}.mp4")
    if has_audio:
        log.info("Merging video + audio...")
        if not merge_audio(concat_path, audio_path, final_path):
            final_path = concat_path
    else:
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

    # 8 — Appwrite
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
        "quality_score": 92,
    })

    return {
        **result,
        "s3_video_url": s3_video_url,
        "s3_thumb_url": s3_thumb_url,
        "has_audio": has_audio,
        "clips_count": len(clip_paths),
    }
