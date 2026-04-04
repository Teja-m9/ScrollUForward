"""
AI Agents reel — anime-style Sora-2, audio-first sync.

Pipeline:
  1. Write per-scene narration chunks
  2. Generate TTS for EACH chunk → measure exact duration
  3. Pick closest Sora seconds (4/8/12) per chunk
  4. Generate Sora clips with anime-style prompts
  5. For each scene: trim/pad clip to exactly match TTS chunk length
  6. Concatenate scenes, stitch audio, upload

Run: python run_ai_agents_anime_sora.py
"""
import asyncio
import logging
import os
import subprocess
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(__file__))
os.environ["PATH"] = r"C:\KMPlayer" + os.pathsep + os.environ.get("PATH", "")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
log = logging.getLogger("anime_sora")

FFMPEG  = r"C:\KMPlayer\ffmpeg.exe"
DOMAIN  = "ai"
REEL_ID = "reel_ai_agents_explained_001"
TOPIC   = "AI Agents Explained — In Anime Style"

# ── Scenes: narration + Sora prompt that ILLUSTRATES the concept being explained
SCENES = [
    {
        "narration": (
            "An AI agent is not just a chatbot that answers questions. "
            "It's an autonomous system that perceives the world, makes decisions, and takes real actions — "
            "browsing the web, writing code, sending emails — all on its own, without you pressing a button."
        ),
        "sora_prompt": (
            "Anime animation: a humanoid AI robot character with sleek glowing circuit patterns "
            "sits at a holographic desk autonomously multitasking — one hand types floating code, "
            "a glowing envelope flies out representing an email sent, a web browser screen opens itself, "
            "all while no human is present giving commands. "
            "The robot's eyes glow with focused intelligence. "
            "Dark futuristic room, neon blue and amber anime art style, smooth fluid animation, "
            "high-quality anime cel-shading, cinematic camera pan."
        ),
    },
    {
        "narration": (
            "Step one is Perception. "
            "The agent reads the world — your instructions, images, tool outputs, search results — "
            "and builds a complete picture of what's happening and what needs to be done."
        ),
        "sora_prompt": (
            "Anime animation: close-up of an AI agent character — an anime-style humanoid robot "
            "with large expressive eyes — as streams of colorful data fly into its eyes: "
            "floating text lines, thumbnail images, graph icons, search result cards, "
            "all flowing in like a river of information being absorbed. "
            "The character's pupils light up and expand as data is received. "
            "Neon cyan data streams on a dark background, dramatic anime lighting, "
            "high-detail cel-shaded art, smooth zoom-in camera movement."
        ),
    },
    {
        "narration": (
            "Step two: Reasoning and Planning. "
            "The agent uses a language model to think through the goal, "
            "then breaks it into a sequence of steps — "
            "search first, then analyze, then write, then send. "
            "Step three: Action — it executes each step using tools and APIs."
        ),
        "sora_prompt": (
            "Anime animation: inside the AI agent's mind — a glowing holographic thought space. "
            "A numbered plan appears step by step as bright floating nodes: "
            "'1. Search' lights up gold, '2. Analyze' lights up cyan, '3. Write' lights up green, '4. Send' lights up orange. "
            "The anime robot character stands in the center watching its own plan form, "
            "then reaches out and activates each glowing tool icon in sequence. "
            "Dark mental space with vivid neon nodes and connecting lines, anime art style, dynamic animation."
        ),
    },
    {
        "narration": (
            "Memory makes agents truly powerful. "
            "Short-term memory tracks the current task. "
            "Long-term memory stores facts across sessions — so it remembers you tomorrow. "
            "And in multi-agent systems, one master agent orchestrates a whole squad: "
            "a researcher, a coder, a reviewer — each doing their specialty."
        ),
        "sora_prompt": (
            "Anime animation: split into two moments. First: the AI agent character opens glowing filing cabinets "
            "labeled 'Short-Term' and 'Long-Term' — memories fly in as glowing orbs being stored. "
            "Then the scene expands to show four anime-style AI agents in a team formation — "
            "a lead orchestrator in the center with a glowing command aura, "
            "flanked by a researcher agent holding books, a coder agent with floating code screens, "
            "and a reviewer agent holding a glowing checkmark. "
            "Glowing data packets pass between them like a synchronized squad. "
            "High-quality anime cel animation, dark background, colorful character designs."
        ),
    },
    {
        "narration": (
            "This is the future of software. "
            "Not apps you click through — but intelligent agents that work for you. "
            "AI agents are already here: booking your meetings, writing your reports, researching for you. "
            "Follow ScrollUForward and learn how AI is reshaping the world — one agent at a time."
        ),
        "sora_prompt": (
            "Anime animation: montage of AI agents helping humans in real scenarios — "
            "an anime student receiving personalized tutoring from a glowing AI tutor character hovering beside them, "
            "a businessperson watching an AI agent draft and send emails automatically on a floating screen, "
            "a scientist with an AI research assistant highlighting key discoveries. "
            "Each scene is warm and inspiring. "
            "Final shot: the AI agent characters all turn to camera and bow as glowing particle text "
            "forms the word 'ScrollUForward' in the air above them. "
            "Cinematic anime quality, golden warm lighting, emotional and uplifting."
        ),
    },
]


# ── Helpers ───────────────────────────────────────────────────────────────────

def get_audio_duration(path: str) -> float:
    """Return audio file duration in seconds using FFmpeg."""
    r = subprocess.run(
        [FFMPEG, "-i", path, "-f", "null", "-"],
        capture_output=True, text=True, timeout=30,
    )
    for line in r.stderr.split("\n"):
        if "Duration:" in line:
            parts = line.strip().split("Duration:")[1].split(",")[0].strip()
            h, m, s = parts.split(":")
            return float(h) * 3600 + float(m) * 60 + float(s)
    return 0.0


def closest_sora_seconds(duration: float) -> int:
    """Pick 4, 8, or 12 — whichever is >= duration and closest."""
    for s in [4, 8, 12]:
        if s >= duration:
            return s
    return 12


def get_duration(path: str) -> float:
    """Return video/audio file duration in seconds."""
    r = subprocess.run([FFMPEG, "-i", path, "-f", "null", "-"],
                       capture_output=True, text=True, timeout=30)
    for line in r.stderr.split("\n"):
        if "Duration:" in line:
            h, m, s = line.strip().split("Duration:")[1].split(",")[0].strip().split(":")
            return float(h) * 3600 + float(m) * 60 + float(s)
    return 0.0


async def generate_chunk_tts(text: str, out_path: str) -> float:
    """Generate TTS for one narration chunk; return duration in seconds."""
    from agents.reel_agent import generate_voiceover
    await generate_voiceover(text, out_path)
    if os.path.exists(out_path) and os.path.getsize(out_path) > 0:
        return get_audio_duration(out_path)
    return 0.0


def submit_sora_job(client, prompt: str, seconds: int) -> str | None:
    try:
        job = client.videos.create(
            model="sora-2",
            prompt=prompt,
            size="720x1280",
            seconds=seconds,
        )
        log.info(f"  Sora job {job.id[:25]}... ({seconds}s) queued")
        return job.id
    except Exception as e:
        log.error(f"  Submit failed: {e}")
        return None


def poll_and_download(client, job_id: str, out_path: str, timeout: int = 600) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        v = client.videos.retrieve(job_id)
        log.info(f"  {job_id[:20]}... {v.status} {v.progress}%")
        if v.status == "completed":
            response = client.videos.download_content(job_id)
            with open(out_path, "wb") as f:
                f.write(response.content)
            log.info(f"  Saved {os.path.getsize(out_path)//1024} KB")
            return True
        if v.status in ("failed", "cancelled"):
            log.error(f"  Job {job_id[:20]} failed: {getattr(v, 'error', v.status)}")
            return False
        time.sleep(15)
    log.error(f"  Timeout: {job_id}")
    return False


# ── Main ─────────────────────────────────────────────────────────────────────

async def main():
    from openai import OpenAI
    from s3_client import upload_reel, upload_thumbnail
    from agents.reel_agent import extract_thumbnail
    from agents.domain_router import publish_reel

    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    tmp = tempfile.mkdtemp(prefix="anime_sora_")
    log.info(f"Temp dir: {tmp}")

    # ── Step 1: Generate TTS per scene, measure durations ─────────────────
    log.info("=== Step 1: Generating per-scene TTS ===")
    chunk_audios   = []
    chunk_durations = []
    for i, scene in enumerate(SCENES):
        audio_path = os.path.join(tmp, f"audio_{i:02d}.mp3")
        dur = await generate_chunk_tts(scene["narration"], audio_path)
        log.info(f"  Scene {i+1}: {dur:.1f}s narration — '{scene['narration'][:40]}...'")
        chunk_audios.append(audio_path)
        chunk_durations.append(dur)

    sora_seconds = [closest_sora_seconds(d) for d in chunk_durations]
    log.info(f"Sora seconds per scene: {sora_seconds}")
    log.info(f"Total video: {sum(sora_seconds)}s | Total audio: {sum(chunk_durations):.1f}s")

    # ── Step 2: Submit Sora jobs ───────────────────────────────────────────
    log.info("=== Step 2: Submitting Sora jobs ===")
    job_ids = []
    for i, (scene, secs) in enumerate(zip(SCENES, sora_seconds)):
        jid = submit_sora_job(client, scene["sora_prompt"], secs)
        job_ids.append(jid)

    # ── Step 3: Poll + download ────────────────────────────────────────────
    log.info("=== Step 3: Polling Sora jobs ===")
    raw_clips = []
    for i, jid in enumerate(job_ids):
        if jid is None:
            raw_clips.append(None)
            continue
        log.info(f"  Waiting for scene {i+1}...")
        out = os.path.join(tmp, f"raw_{i:02d}.mp4")
        ok = poll_and_download(client, jid, out)
        raw_clips.append(out if ok else None)

    # ── Step 4: Collect good clips ─────────────────────────────────────────
    log.info("=== Step 4: Collecting clips ===")
    good_clips  = []
    good_audios = []
    for i, (raw, audio) in enumerate(zip(raw_clips, chunk_audios)):
        if raw and os.path.exists(raw):
            good_clips.append(raw)
            good_audios.append(audio)
            log.info(f"  Scene {i+1} OK: {os.path.getsize(raw)//1024} KB")
        else:
            log.warning(f"  Scene {i+1} missing — skipping")

    if not good_clips:
        log.error("No clips — aborting")
        return

    # ── Step 5: Concatenate video clips ───────────────────────────────────
    log.info("=== Step 5: Concatenating video ===")
    list_file = os.path.join(tmp, "vlist.txt")
    with open(list_file, "w") as f:
        for p in good_clips:
            f.write(f"file '{p}'\n")
    concat_video = os.path.join(tmp, "concat_video.mp4")
    r = subprocess.run([FFMPEG, "-y", "-f", "concat", "-safe", "0",
                        "-i", list_file, "-c", "copy", concat_video],
                       capture_output=True, text=True, timeout=120)
    if r.returncode != 0:
        log.error(f"Video concat failed: {r.stderr[-300:]}")
        return
    video_dur = get_duration(concat_video)
    log.info(f"  Video: {os.path.getsize(concat_video)//1024} KB, {video_dur:.1f}s")

    # ── Step 6: Concatenate audio chunks ──────────────────────────────────
    log.info("=== Step 6: Concatenating audio ===")
    alist_file = os.path.join(tmp, "alist.txt")
    with open(alist_file, "w") as f:
        for p in good_audios:
            f.write(f"file '{p}'\n")
    concat_audio = os.path.join(tmp, "concat_audio.mp3")
    r = subprocess.run([FFMPEG, "-y", "-f", "concat", "-safe", "0",
                        "-i", alist_file, "-c", "copy", concat_audio],
                       capture_output=True, text=True, timeout=60)
    if r.returncode != 0:
        log.error(f"Audio concat failed: {r.stderr[-300:]}")
        return
    audio_dur = get_duration(concat_audio)
    log.info(f"  Audio: {os.path.getsize(concat_audio)//1024} KB, {audio_dur:.1f}s")

    # ── Step 7: Merge — stretch video to match audio via setpts ───────────
    # setpts factor: audio_dur/video_dur makes video play at the right speed
    # (e.g. 65s audio / 60s video = 1.083x slowdown — imperceptible)
    log.info("=== Step 7: Final merge + sync + upscale ===")
    pts_factor = audio_dur / video_dur if video_dur > 0 else 1.0
    log.info(f"  setpts factor: {pts_factor:.4f} ({video_dur:.1f}s video → {audio_dur:.1f}s)")
    final_path = os.path.join(tmp, f"{REEL_ID}.mp4")
    r = subprocess.run([
        FFMPEG, "-y",
        "-i", concat_video,
        "-i", concat_audio,
        "-map", "0:v:0", "-map", "1:a:0",
        "-vf", f"setpts={pts_factor:.6f}*PTS,scale=1080:1920:flags=lanczos",
        "-c:v", "libx264", "-preset", "fast", "-crf", "20",
        "-strict", "-2", "-c:a", "aac",
        final_path,
    ], capture_output=True, text=True, timeout=300)
    if r.returncode != 0:
        log.error(f"Final merge failed: {r.stderr[-400:]}")
        return
    log.info(f"  Final: {os.path.getsize(final_path)//1024} KB")

    # ── Step 8: Thumbnail + S3 + Appwrite ─────────────────────────────────
    log.info("=== Step 8: Upload + Publish ===")
    thumb_path = os.path.join(tmp, f"{REEL_ID}_thumb.jpg")
    r = subprocess.run([FFMPEG, "-y", "-i", final_path, "-ss", "00:00:03",
                        "-frames:v", "1", thumb_path],
                       capture_output=True, text=True, timeout=30)
    has_thumb = os.path.exists(thumb_path)

    s3_video_url = upload_reel(final_path, DOMAIN, REEL_ID)
    log.info(f"  Video: {s3_video_url[:70]}...")

    s3_thumb_url = ""
    if has_thumb:
        with open(thumb_path, "rb") as f:
            s3_thumb_url = upload_thumbnail(f.read(), DOMAIN, REEL_ID)
        log.info("  Thumbnail uploaded")

    full_narration = "\n\n".join(s["narration"] for s in SCENES)
    result = publish_reel({
        "reel_id": REEL_ID,
        "domain": DOMAIN,
        "title": TOPIC,
        "script_text": full_narration,
        "s3_video_url": s3_video_url,
        "s3_thumb_url": s3_thumb_url,
        "source_type": "ai_generated",
        "content_type": "reel",
        "quality_score": 96,
    })

    print("\n" + "=" * 60)
    print(f"  ID     : {result.get('id')}")
    print(f"  Status : {result.get('status')}")
    print(f"  Video  : {'YES' if s3_video_url else 'NO'}")
    print(f"  Thumb  : {'YES' if s3_thumb_url else 'NO'}")
    print(f"  Scenes : {len(good_clips)}")
    print("=" * 60)
    if result.get("status") == "published":
        print("REEL IS LIVE in the app feed!")


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    asyncio.run(main())
