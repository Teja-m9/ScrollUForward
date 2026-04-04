"""
F1 Racing reel — pure Manim + Deepgram TTS.
Run: python run_f1_reel.py
"""
import asyncio, logging, os, subprocess, sys, tempfile

sys.path.insert(0, os.path.dirname(__file__))
os.environ["PATH"] = r"C:\KMPlayer" + os.pathsep + os.environ.get("PATH", "")

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s")
log = logging.getLogger("f1_reel")

FFMPEG     = r"C:\KMPlayer\ffmpeg.exe"
TOPIC      = "Formula One — The Greatest Drivers of All Time"
DOMAIN     = "technology"
REEL_ID    = "reel_f1_racing_001"
SCENE_FILE = "f1_reel.py"

NARRATION = """
Formula One is the pinnacle of motorsport —
where the fastest machines on Earth push the limits of physics,
engineering, and human courage at over three hundred kilometres per hour.

Since nineteen fifty, the World Drivers Championship has crowned legends.
But who are the greatest of all time?

Ayrton Senna — three world championships.
A genius in the rain, whose lap at Monaco nineteen eighty-four
is still called the greatest single lap ever driven.

Alain Prost — four world titles.
The Professor. Cold, calculating, devastatingly precise.
One hundred and six podiums across sixteen seasons.

Michael Schumacher — seven world championships.
Unmatched for a generation. His record seemed untouchable.
Ninety-one race victories. A legend of the sport.

Sebastian Vettel — four consecutive titles with Red Bull.
Youngest world champion in history at twenty-three.

Fernando Alonso — two championships, and arguably the most complete driver ever.
Still racing, still challenging, decades after his debut.

Then came Lewis Hamilton — seven world championships.
One hundred and three race wins. The most decorated driver in history,
now chasing an eighth title with Ferrari.

And Max Verstappen — four consecutive world championships with Red Bull,
dominating the modern era with raw speed and ruthless precision.

This is Formula One.
The fastest sport on the planet. The greatest drivers who ever lived.

Follow ScrollUForward — learn something real every day.
"""


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
    from agents.reel_agent import generate_voiceover
    from agents.domain_router import publish_reel
    from s3_client import upload_reel, upload_thumbnail

    tmp        = tempfile.mkdtemp(prefix="f1_reel_")
    scenes_dir = os.path.join(os.path.dirname(__file__), "scenes")
    scene_path = os.path.join(scenes_dir, SCENE_FILE)
    media_dir  = os.path.join(tmp, "media")

    log.info(f"Reel  : {REEL_ID}")
    log.info(f"Tmp   : {tmp}")

    # ── 1. TTS ────────────────────────────────────────────────────────
    log.info("=== Step 1: TTS narration ===")
    audio_path = os.path.join(tmp, "narration.mp3")
    await generate_voiceover(NARRATION.strip(), audio_path)
    has_audio = os.path.exists(audio_path) and os.path.getsize(audio_path) > 0
    if has_audio:
        audio_dur = get_duration(audio_path)
        log.info(f"  TTS: {os.path.getsize(audio_path)//1024} KB, {audio_dur:.1f}s")
    else:
        log.warning("  TTS failed")
        audio_dur = 0.0

    # ── 2. Manim render ───────────────────────────────────────────────
    log.info("=== Step 2: Rendering Manim scene ===")
    r = subprocess.run([
        sys.executable, "-m", "manim", "render",
        scene_path, "ReelScene",
        "-r", "540,960", "--fps", "30", "--format=mp4",
        f"--media_dir={media_dir}", "--disable_caching",
    ], capture_output=True, text=True, timeout=600)

    if r.returncode != 0:
        log.error(f"Manim failed:\n{r.stderr[-1500:]}")
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

    # ── 3. Sync: stretch video to match audio, upscale ────────────────
    log.info("=== Step 3: Sync video to audio + upscale ===")
    final_path = os.path.join(tmp, f"{REEL_ID}.mp4")
    if has_audio and video_dur > 0:
        pts = audio_dur / video_dur
        log.info(f"  setpts={pts:.4f}  ({video_dur:.1f}s → {audio_dur:.1f}s)")
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
        log.error(f"FFmpeg failed:\n{r.stderr[-500:]}")
        final_path = manim_mp4
    else:
        log.info(f"  Final: {os.path.getsize(final_path)//1024} KB")

    # ── 4. Thumbnail + S3 + Appwrite ─────────────────────────────────
    log.info("=== Step 4: Upload + Publish ===")
    thumb_path = os.path.join(tmp, f"{REEL_ID}_thumb.jpg")
    subprocess.run([FFMPEG, "-y", "-i", final_path,
                    "-ss", "00:00:04", "-frames:v", "1", thumb_path],
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
        "quality_score": 94,
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
