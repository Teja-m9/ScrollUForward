"""
Kurzgesagt-style reel pipeline — no character overlay.
Pure Manim animation + Deepgram TTS + FFmpeg + S3 + Appwrite.
Run: python run_kurzgesagt_reel.py
"""
import asyncio, logging, sys, os, subprocess, tempfile, uuid

sys.path.insert(0, os.path.dirname(__file__))
os.environ["PATH"] = r"C:\KMPlayer" + os.pathsep + os.environ.get("PATH", "")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
log = logging.getLogger("kurzgesagt")

TOPIC      = "What Happens Inside a Black Hole"
DOMAIN     = "space"
REEL_ID    = "reel_kurzgesagt_blackhole_002"
SCENE_FILE = "kurzgesagt_blackhole_reel.py"
NARRATION  = """
What if you fell into a black hole? Not a movie black hole — a real one.

First: the event horizon. This invisible boundary is the point of no return.
Cross it, and not even light can escape. From the outside, you would appear
to freeze in time, glowing redder and dimmer for eternity. But from your
perspective? You'd sail right through — you might not even notice.

Then comes spaghettification. Because gravity is so much stronger near a
black hole, your feet feel a far greater pull than your head. This tidal
difference stretches you — literally — into a long strand of particles.
Scientists actually call this spaghettification.

At the center lies the singularity. A point of theoretically infinite density
and zero volume. Here, every equation we have breaks down completely. General
relativity fails. Quantum mechanics fails. We genuinely don't know what exists
at the singularity — or what happens to information that falls in.

Black holes aren't cosmic vacuum cleaners. They don't suck things in. They
simply curve space so sharply that nothing nearby can escape their geometry.

They are the universe's way of telling us: you don't understand everything yet.

Explore more fascinating science on ScrollUForward. Learn something real every day.
"""


async def main():
    from agents.reel_agent import generate_voiceover, assemble_reel, extract_thumbnail
    from agents.domain_router import publish_reel
    from s3_client import upload_reel, upload_thumbnail

    tmp = tempfile.mkdtemp(prefix="kurzgesagt_")
    scenes_dir = os.path.join(os.path.dirname(__file__), "scenes")
    scene_path = os.path.join(scenes_dir, SCENE_FILE)
    media_dir  = os.path.join(tmp, "media")

    log.info(f"Topic : {TOPIC}")
    log.info(f"Reel  : {REEL_ID}")

    # 1. Render Manim
    log.info("Rendering Manim scene...")
    render_cmd = [
        sys.executable, "-m", "manim", "render",
        scene_path, "ReelScene",
        "-r", "540,960", "--fps", "30", "--format=mp4",
        f"--media_dir={media_dir}", "--disable_caching",
    ]
    result = subprocess.run(render_cmd, capture_output=True, text=True, timeout=300)
    if result.returncode != 0:
        log.error(f"Manim failed:\n{result.stderr[-800:]}")
        return

    manim_mp4 = ""
    for root, dirs, files in os.walk(media_dir):
        for f in files:
            if f.endswith(".mp4") and "partial" not in root:
                manim_mp4 = os.path.join(root, f)
                break
        if manim_mp4:
            break

    if not manim_mp4:
        log.error("No MP4 found after Manim render")
        return
    log.info(f"Manim rendered: {os.path.getsize(manim_mp4)//1024} KB")

    # 2. Deepgram TTS
    audio_path = os.path.join(tmp, "narration.mp3")
    log.info("Generating TTS...")
    await generate_voiceover(NARRATION.strip(), audio_path)
    has_audio = os.path.exists(audio_path) and os.path.getsize(audio_path) > 0
    if has_audio:
        log.info(f"TTS generated: {os.path.getsize(audio_path)//1024} KB")
    else:
        log.warning("TTS failed, proceeding without audio")

    # 3. FFmpeg: merge video + audio, upscale to 1080x1920
    output_mp4 = os.path.join(tmp, f"{REEL_ID}.mp4")
    log.info("Assembling with FFmpeg...")
    assembled = assemble_reel(manim_mp4, audio_path if has_audio else "", output_mp4)
    final_mp4 = assembled if assembled else manim_mp4
    log.info(f"Final video: {os.path.getsize(final_mp4)//1024} KB")

    # 4. Upload to S3
    log.info("Uploading to S3...")
    s3_video_url = upload_reel(final_mp4, DOMAIN, REEL_ID)
    log.info(f"Video URL: {s3_video_url[:80]}...")

    s3_thumb_url = ""
    thumb_path = os.path.join(tmp, f"{REEL_ID}_thumb.jpg")
    if extract_thumbnail(final_mp4, thumb_path):
        with open(thumb_path, "rb") as f:
            s3_thumb_url = upload_thumbnail(f.read(), DOMAIN, REEL_ID)
        log.info("Thumbnail uploaded")

    # 5. Publish to Appwrite
    log.info("Publishing to Appwrite...")
    result = publish_reel({
        "reel_id": REEL_ID,
        "domain": DOMAIN,
        "title": TOPIC,
        "script_text": NARRATION.strip(),
        "s3_video_url": s3_video_url,
        "s3_thumb_url": s3_thumb_url,
        "source_type": "ai_generated",
        "content_type": "reel",
        "quality_score": 92,
    })

    print("\n" + "=" * 60)
    print(f"  ID     : {result.get('id')}")
    print(f"  Status : {result.get('status')}")
    print(f"  Title  : {TOPIC}")
    print(f"  Video  : {'YES' if s3_video_url else 'NO'}")
    print(f"  Audio  : {'YES' if has_audio else 'NO'}")
    print(f"  Thumb  : {'YES' if s3_thumb_url else 'NO'}")
    print("=" * 60)
    if result.get("status") == "published":
        print("REEL IS LIVE in the app feed!")


if __name__ == "__main__":
    asyncio.run(main())
