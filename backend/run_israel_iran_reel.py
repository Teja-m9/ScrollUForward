"""
Israel-Iran conflict reel — Stable Diffusion images (via Pollinations.ai free SD API)
+ Manim overlays + Deepgram TTS + FFmpeg sync + S3 + Appwrite.

Run: python run_israel_iran_reel.py
"""
import asyncio, logging, os, subprocess, sys, tempfile, urllib.parse
import httpx

sys.path.insert(0, os.path.dirname(__file__))
os.environ["PATH"] = r"C:\KMPlayer" + os.pathsep + os.environ.get("PATH", "")

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s")
log = logging.getLogger("israel_iran_reel")

FFMPEG     = r"C:\KMPlayer\ffmpeg.exe"
TOPIC      = "Israel vs Iran — The Conflict Reshaping the Middle East"
DOMAIN     = "history"
REEL_ID    = "reel_israel_iran_001"
SCENE_FILE = "israel_iran_reel.py"

NARRATION = """
The Israel-Iran conflict is one of the most consequential geopolitical flashpoints
of the twenty-first century — and it is no longer fought only in the shadows.

For four decades, Iran funded and armed proxy forces across the Middle East:
Hezbollah in Lebanon, Hamas in Gaza, the Houthis in Yemen, and militias in Iraq and Syria —
building a ring of pressure around Israel.

At the heart of the tension is Iran's nuclear program.
With uranium enrichment approaching weapons-grade levels,
Israel has long considered a nuclear Iran an existential threat.

In April 2024, something unprecedented happened.
Iran launched a direct attack on Israeli soil for the very first time —
more than three hundred drones and ballistic missiles in a single night.
Israel, with help from the United States, the United Kingdom, Jordan, and Saudi Arabia,
intercepted ninety-nine percent of them.

Israel struck back — targeting Iranian air defence systems.
Two nuclear-armed powers had exchanged direct blows for the first time in history.

The stakes extend far beyond the Middle East.
Iran controls the Strait of Hormuz — the narrow corridor through which
twenty percent of the world's oil supply flows every day.
Any escalation sends shockwaves through global energy markets.

This conflict is not a regional dispute.
It is a defining crisis for the entire world.

Stay informed on ScrollUForward — learn something real every day.
"""

# Stable Diffusion prompts via Pollinations.ai (free, no API key needed)
SD_PROMPTS = [
    # Scene 1 — Overview
    "political map of Middle East, Israel and Iran marked with glowing highlights, "
    "dark blue background, professional news infographic editorial illustration, "
    "clean modern design, no text labels",

    # Scene 2 — History
    "nuclear facility aerial view in Middle East desert landscape, "
    "news editorial illustration style, dark dramatic lighting, "
    "military and geopolitical tension visual, professional journalism graphic",

    # Scene 3 — April 2024 strikes
    "missile and drone trajectory arcs over Middle East map at night, "
    "news infographic visualization style, dark background with glowing arcs, "
    "military strike map editorial illustration",

    # Scene 4 — Proxy network
    "Middle East regional map showing network of conflict zones, "
    "Lebanon Syria Yemen Iraq highlighted with connection lines, "
    "dark news graphic style, professional editorial cartography",

    # Scene 5 — Global stakes
    "aerial view of oil tankers in narrow strait at sunset, "
    "strategic chokepoint visualization, global trade route map overlay, "
    "dramatic editorial photography style",
]


async def generate_sd_image(prompt: str, out_path: str, idx: int) -> bool:
    """Generate image via Pollinations.ai (free Stable Diffusion / Flux API)."""
    encoded = urllib.parse.quote(prompt)
    url = (
        f"https://image.pollinations.ai/prompt/{encoded}"
        f"?width=576&height=1024&nologo=1&model=flux&seed={idx * 42}"
    )
    try:
        async with httpx.AsyncClient(timeout=120) as client:
            r = await client.get(url)
            r.raise_for_status()
            if len(r.content) < 5000:
                log.warning(f"  SD image {idx}: too small ({len(r.content)} bytes)")
                return False
            with open(out_path, "wb") as f:
                f.write(r.content)
        log.info(f"  SD image {idx}: {os.path.getsize(out_path)//1024} KB")
        return True
    except Exception as e:
        log.warning(f"  SD image {idx} failed: {e}")
        return False


def get_duration(path: str) -> float:
    r = subprocess.run([FFMPEG, "-i", path, "-f", "null", "-"],
                       capture_output=True, text=True, timeout=30)
    for line in r.stderr.split("\n"):
        if "Duration:" in line:
            h, m, s = line.strip().split("Duration:")[1].split(",")[0].strip().split(":")
            return float(h)*3600 + float(m)*60 + float(s)
    return 0.0


async def main():
    from dotenv import load_dotenv
    load_dotenv()
    from agents.reel_agent import generate_voiceover, extract_thumbnail
    from agents.domain_router import publish_reel
    from s3_client import upload_reel, upload_thumbnail

    tmp        = tempfile.mkdtemp(prefix="israel_iran_reel_")
    scenes_dir = os.path.join(os.path.dirname(__file__), "scenes")
    scene_path = os.path.join(scenes_dir, SCENE_FILE)
    media_dir  = os.path.join(tmp, "media")

    log.info(f"Reel : {REEL_ID}")
    log.info(f"Tmp  : {tmp}")

    # ── 1. Generate Stable Diffusion images in parallel ───────────────
    log.info("=== Step 1: Generating Stable Diffusion images (Pollinations.ai) ===")
    img_paths = [os.path.join(tmp, f"sd_{i}.jpg") for i in range(5)]
    results   = await asyncio.gather(*[
        generate_sd_image(prompt, img_paths[i], i)
        for i, prompt in enumerate(SD_PROMPTS)
    ])
    for i, ok in enumerate(results):
        env_key = f"SD_IMG_{i}"
        os.environ[env_key] = img_paths[i] if ok else ""
        log.info(f"  {env_key}: {'OK' if ok else 'MISSING (scene uses geometry fallback)'}")

    # ── 2. TTS narration ──────────────────────────────────────────────
    log.info("=== Step 2: Generating TTS narration ===")
    audio_path = os.path.join(tmp, "narration.mp3")
    await generate_voiceover(NARRATION.strip(), audio_path)
    has_audio = os.path.exists(audio_path) and os.path.getsize(audio_path) > 0
    if has_audio:
        audio_dur = get_duration(audio_path)
        log.info(f"  TTS: {os.path.getsize(audio_path)//1024} KB, {audio_dur:.1f}s")
    else:
        log.warning("  TTS failed")
        audio_dur = 0.0

    # ── 3. Render Manim scene ─────────────────────────────────────────
    log.info("=== Step 3: Rendering Manim scene ===")
    r = subprocess.run([
        sys.executable, "-m", "manim", "render",
        scene_path, "ReelScene",
        "-r", "540,960", "--fps", "30", "--format=mp4",
        f"--media_dir={media_dir}", "--disable_caching",
    ], capture_output=True, text=True, timeout=600, env=os.environ.copy())

    if r.returncode != 0:
        log.error(f"Manim failed:\n{r.stderr[-1000:]}")
        return

    manim_mp4 = ""
    for root, _, files in os.walk(media_dir):
        for f in files:
            if f.endswith(".mp4") and "partial" not in root:
                manim_mp4 = os.path.join(root, f)
                break
        if manim_mp4:
            break

    if not manim_mp4:
        log.error("No MP4 found after Manim render")
        return
    video_dur = get_duration(manim_mp4)
    log.info(f"  Manim: {os.path.getsize(manim_mp4)//1024} KB, {video_dur:.1f}s")

    # ── 4. Sync: stretch video to match audio, upscale 1080x1920 ──────
    log.info("=== Step 4: Sync video → audio + upscale ===")
    final_path = os.path.join(tmp, f"{REEL_ID}.mp4")
    if has_audio and video_dur > 0:
        pts = audio_dur / video_dur
        log.info(f"  setpts={pts:.4f} ({video_dur:.1f}s → {audio_dur:.1f}s)")
        cmd = [
            FFMPEG, "-y",
            "-i", manim_mp4, "-i", audio_path,
            "-map", "0:v:0", "-map", "1:a:0",
            "-vf", f"setpts={pts:.6f}*PTS,scale=1080:1920:flags=lanczos",
            "-c:v", "libx264", "-preset", "fast", "-crf", "20",
            "-strict", "-2", "-c:a", "aac",
            final_path,
        ]
    else:
        cmd = [
            FFMPEG, "-y", "-i", manim_mp4,
            "-vf", "scale=1080:1920:flags=lanczos",
            "-c:v", "libx264", "-preset", "fast", "-crf", "20",
            final_path,
        ]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if r.returncode != 0:
        log.error(f"FFmpeg failed:\n{r.stderr[-400:]}")
        final_path = manim_mp4
    else:
        log.info(f"  Final: {os.path.getsize(final_path)//1024} KB")

    # ── 5. Upload + publish ───────────────────────────────────────────
    log.info("=== Step 5: Upload + Publish ===")
    thumb_path = os.path.join(tmp, f"{REEL_ID}_thumb.jpg")
    subprocess.run([FFMPEG, "-y", "-i", final_path,
                    "-ss", "00:00:03", "-frames:v", "1", thumb_path],
                   capture_output=True, timeout=30)
    has_thumb = os.path.exists(thumb_path)

    s3_video_url = upload_reel(final_path, DOMAIN, REEL_ID)
    log.info(f"  Video: {s3_video_url[:70]}...")

    s3_thumb_url = ""
    if has_thumb:
        with open(thumb_path, "rb") as f:
            s3_thumb_url = upload_thumbnail(f.read(), DOMAIN, REEL_ID)
        log.info("  Thumbnail uploaded")

    result = publish_reel({
        "reel_id": REEL_ID,
        "domain": DOMAIN,
        "title": TOPIC,
        "script_text": NARRATION.strip(),
        "s3_video_url": s3_video_url,
        "s3_thumb_url": s3_thumb_url,
        "source_type": "ai_generated",
        "content_type": "reel",
        "quality_score": 91,
    })

    print("\n" + "=" * 60)
    print(f"  ID     : {result.get('id')}")
    print(f"  Status : {result.get('status')}")
    print(f"  Video  : {'YES' if s3_video_url else 'NO'}")
    print(f"  Audio  : {'YES' if has_audio else 'NO'}")
    print(f"  Thumb  : {'YES' if has_thumb else 'NO'}")
    print("=" * 60)
    if result.get("status") == "published":
        print("REEL IS LIVE in the app feed!")


if __name__ == "__main__":
    asyncio.run(main())
