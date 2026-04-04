"""
Reel Agent — AI Video Generation via Groq + Manim CE

Pipeline:
  1. Research topic (SerpAPI / Groq fallback)
  2. Groq writes a cinematic story-based narration + scene plan
  3. Groq generates Manim CE code with smooth animations + transitions
  4. Manim CE renders vertical 9:16 MP4
  5. ElevenLabs TTS narration audio
  6. FFmpeg merges video + audio, upscales to 1080x1920
  7. Upload to S3, publish metadata to Appwrite
"""
import os
import sys
import json
import uuid
import tempfile
import subprocess
import logging
import asyncio
import re
from datetime import datetime

import httpx
from groq import Groq
from tenacity import retry, stop_after_attempt, wait_exponential

from config import (
    GROQ_API_KEY, GROQ_MODEL_PRIMARY,
    DEEPGRAM_API_KEY, SERPAPI_KEY,
)
from s3_client import upload_reel, upload_thumbnail

logger = logging.getLogger(__name__)

# Render at half-res vertical, upscale with FFmpeg
RENDER_W, RENDER_H = 540, 960
OUTPUT_W, OUTPUT_H = 1080, 1920


def _get_groq():
    return Groq(api_key=GROQ_API_KEY)


# ── Step 1: Topic Research ────────────────────────────────
async def research_topic(domain):
    if SERPAPI_KEY:
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(
                    "https://serpapi.com/search.json",
                    params={"q": f"latest {domain} discovery 2025", "api_key": SERPAPI_KEY, "num": 5},
                )
                results = resp.json().get("organic_results", [])
                if results:
                    return {
                        "topic": results[0].get("title", f"Latest in {domain}"),
                        "snippet": results[0].get("snippet", ""),
                    }
        except Exception as e:
            logger.warning(f"SerpAPI failed: {e}")

    groq = _get_groq()
    resp = groq.chat.completions.create(
        model=GROQ_MODEL_PRIMARY,
        messages=[
            {"role": "system", "content": f"Suggest one trending educational topic in {domain}. Reply with just the topic title."},
            {"role": "user", "content": f"What's a fascinating recent topic in {domain}?"},
        ],
        max_tokens=50,
    )
    return {"topic": resp.choices[0].message.content.strip(), "snippet": ""}


# ── Step 2: Plan the Video (Story-Based) ──────────────────
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def plan_video(topic: str, domain: str) -> dict:
    groq = _get_groq()
    resp = groq.chat.completions.create(
        model=GROQ_MODEL_PRIMARY,
        messages=[
            {"role": "system", "content": (
                "You are a 3Blue1Brown-style storyteller planning a 60-90 second animated short. "
                "Write a FLOWING STORY narration — not bullet points. Mini documentary style: "
                "one idea leads naturally into the next, building curiosity and wonder.\n\n"
                "The animation will be rendered by Manim CE in VERTICAL 9:16 format for mobile.\n\n"
                "Return ONLY a JSON object:\n"
                "{\n"
                '  "title": "Short catchy title (max 50 chars)",\n'
                '  "narration": "A single flowing 200-280 word story narration for the voiceover.",\n'
                '  "scenes": [\n'
                '    {"name": "hook", "duration": 12, '
                '"transcript": "Short subtitle text shown on screen during this scene (1-2 sentences, max 15 words)", '
                '"visual": "TOPIC-SPECIFIC Manim visual: describe exactly what shapes/diagrams represent the actual subject"},\n'
                '    {"name": "concept", "duration": 15, '
                '"transcript": "Subtitle for this scene", '
                '"visual": "e.g. For chemistry: circles as atoms with + and - labels, arrows showing electron flow, bonds forming"},\n'
                '    {"name": "build", "duration": 15, '
                '"transcript": "Subtitle for this scene", '
                '"visual": "e.g. For batteries: rectangle as battery cell, ions flowing left to right, voltage graph building"},\n'
                '    {"name": "reveal", "duration": 15, '
                '"transcript": "Subtitle for this scene", '
                '"visual": "e.g. Side-by-side comparison diagram, arrows showing transformation, labels with real data"},\n'
                '    {"name": "wow", "duration": 12, '
                '"transcript": "Subtitle for this scene", '
                '"visual": "e.g. All elements connect into one unified diagram, Flash highlight on the key insight"},\n'
                '    {"name": "close", "duration": 8, '
                '"transcript": "Closing thought subtitle", '
                '"visual": "Title text fades in with surrounding glow rectangle"}\n'
                "  ],\n"
                '  "color_palette": {"background": "#1a1a2e", "primary": "#00d4ff", "secondary": "#ff6b35", "text": "#ffffff"}\n'
                "}\n\n"
                "RULES:\n"
                "- Visuals MUST represent the ACTUAL TOPIC, not generic math graphs. If the topic is\n"
                "  about batteries, show battery diagrams. If about DNA, show helix shapes. If about\n"
                "  planets, show orbits. Use circles/rectangles/arrows/dots creatively as real-world metaphors.\n"
                "- Each scene has a 'transcript' field: short subtitle text shown on screen (max 15 words)\n"
                "- Total duration: 65-80 seconds (minimum 1 minute)\n"
                "- 6 scenes minimum\n"
                "- The story should make a non-expert go 'wow, I never thought of it that way'"
            )},
            {"role": "user", "content": f"Topic: {topic}. Domain: {domain}."},
        ],
        max_tokens=1500,
        temperature=0.7,
    )

    text = resp.choices[0].message.content.strip()
    try:
        if "```" in text:
            text = text.split("```")[1].strip()
            if text.startswith("json"):
                text = text[4:].strip()
        plan = json.loads(text)
        logger.info(f"[ReelAgent] Plan: {plan.get('title', 'untitled')} - {len(plan.get('scenes', []))} scenes")
        return plan
    except json.JSONDecodeError:
        logger.warning("[ReelAgent] Plan JSON parse failed, using fallback")
        return {
            "title": topic,
            "narration": f"Let's explore {topic}. This fascinating concept in {domain} will change how you see the world.",
            "scenes": [
                {"name": "hook", "duration": 8, "visual": f"Title '{topic}' fades in with glow effect"},
                {"name": "build", "duration": 15, "visual": "Animated diagram builds step by step"},
                {"name": "close", "duration": 8, "visual": "Summary text fades in"},
            ],
            "color_palette": {"background": "#1a1a2e", "primary": "#00d4ff", "secondary": "#ff6b35", "text": "#ffffff"},
        }


# ── Step 3: Generate Manim Code ───────────────────────────
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def generate_manim_code(plan: dict) -> str:
    groq = _get_groq()
    scenes_desc = "\n".join(
        f"  Scene {i+1} '{s['name']}' ({s.get('duration', 10)}s):\n"
        f"    Visual: {s['visual']}\n"
        f"    Transcript: \"{s.get('transcript', '')}\""
        for i, s in enumerate(plan.get("scenes", []))
    )
    colors = plan.get("color_palette", {})
    bg = colors.get("background", "#1a1a2e")
    primary = colors.get("primary", "#00d4ff")
    secondary = colors.get("secondary", "#ff6b35")
    text_col = colors.get("text", "#ffffff")

    resp = groq.chat.completions.create(
        model=GROQ_MODEL_PRIMARY,
        messages=[
            {"role": "system", "content": (
                "You are an expert Manim CE v0.20 developer creating STUNNING 3Blue1Brown-quality reels.\n\n"
                "Generate a complete Manim scene for a VERTICAL 9:16 mobile reel. MINIMUM 60 seconds.\n\n"

                "=== SETUP ===\n"
                "`from manim import *`\n"
                "class ReelScene(Scene):\n"
                "  def construct(self):\n"
                f"    self.camera.background_color = '{bg}'\n"
                "    self.camera.frame_width = 6\n"
                "    self.camera.frame_height = 10.67\n\n"

                "=== SCENE CLEANUP (CRITICAL) ===\n"
                "Between EVERY scene: self.play(FadeOut(*self.mobjects), run_time=1)\n"
                "Then create fresh objects. ZERO overlap. Clean screen between scenes.\n\n"

                "=== TOPIC-SPECIFIC VISUALS (MOST IMPORTANT) ===\n"
                "The visuals MUST represent the ACTUAL topic. DO NOT use generic math graphs.\n"
                "- For batteries: rectangles as cells, circles with +/- as ions, arrows as current\n"
                "- For DNA/biology: helix shapes using ParametricFunction, circles as cells\n"
                "- For planets: circles as orbits, dots as planets, size ratios\n"
                "- For chemistry: circles as atoms with element labels, lines as bonds\n"
                "- For AI: circles as neurons, arrows as connections, data flowing\n"
                "Use circles, rectangles, arrows, dots, and Text labels creatively as\n"
                "REAL-WORLD metaphors for the subject matter.\n\n"

                "=== LIVE TRANSCRIPT OVERLAY (EVERY SCENE) ===\n"
                "Each scene MUST show subtitle text at the BOTTOM of the screen:\n"
                "  subtitle = Text('transcript text here', font_size=22, color=WHITE)\n"
                "  subtitle.scale_to_fit_width(4.8)\n"
                "  bg_rect = RoundedRectangle(width=5.2, height=0.8, corner_radius=0.15, "
                "color=BLACK, fill_opacity=0.7, stroke_width=0)\n"
                "  bg_rect.move_to(DOWN*3.5)\n"
                "  subtitle.move_to(bg_rect)\n"
                "  self.play(FadeIn(bg_rect), Write(subtitle), run_time=1.5)\n"
                "The transcript text is provided in each scene description. Show it at y=-3.5.\n"
                "FadeOut the subtitle with everything else at scene end.\n\n"

                "=== ANIMATION TECHNIQUES ===\n"
                "1. LaggedStart for staggered reveals:\n"
                "   self.play(LaggedStart(*[GrowFromCenter(c) for c in items], lag_ratio=0.15), run_time=3)\n"
                "2. Transform chains between scenes for continuity\n"
                "3. NumberPlane + apply_function() for impressive grid warps\n"
                "4. FunctionGraph with tracing Dot for curves\n"
                "5. Arrows with labels for processes and flows\n\n"

                "=== LAYOUT ===\n"
                "- Frame: x=[-2.8, 2.8], y=[-5, 5]\n"
                "- MEDIUM objects: circles 0.3-0.6, rects width 1-2\n"
                "- Main visual centered at ORIGIN to UP*1\n"
                "- Subtitle always at DOWN*4.5 (bottom area)\n"
                "- Scale groups with .scale_to_fit_width(4) if wider\n\n"

                "=== HARD RULES ===\n"
                "- Total: 60-80 seconds. 15-20 self.play() calls.\n"
                "- FadeOut(*self.mobjects) between EVERY scene\n"
                "- NEVER x_min/x_max/y_min/y_max — use x_range/y_range\n"
                "- ALL coords 3D: np.array([x,y,0])\n"
                "- NEVER use MathTex, Tex, ImageMobject\n"
                "- Unicode math: Text('\\u03c0'), Text('Na\\u207a') for Na+\n"
                "- run_time=2-4, self.wait(1-2) between beats\n\n"
                "Return ONLY Python code. No markdown. No explanation."
            )},
            {"role": "user", "content": (
                f"Title: {plan.get('title', 'Educational Video')}\n"
                f"Scenes:\n{scenes_desc}\n"
                f"Colors: bg={bg}, primary={primary}, secondary={secondary}, text={text_col}\n\n"
                f"Create a 60+ second reel. Visuals MUST represent {plan.get('title', 'the topic')} specifically.\n"
                f"Show LIVE TRANSCRIPT subtitles at bottom of every scene.\n"
                f"Clean screen between scenes. Topic-specific shapes, not generic graphs."
            )},
        ],
        max_tokens=6000,
        temperature=0.4,
    )

    code = resp.choices[0].message.content.strip()

    # Strip markdown fences
    if code.startswith("```"):
        lines = code.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        code = "\n".join(lines)

    # Ensure import
    if "from manim import" not in code:
        code = "from manim import *\n\n" + code

    # Ensure class name
    if "class ReelScene" not in code:
        if "class " in code:
            code = re.sub(r'class \w+\(Scene\)', 'class ReelScene(Scene)', code, count=1)
        else:
            code = code  # will fail at render, auto-fix will catch it

    # Safety: replace LaTeX objects with Text
    code = re.sub(r'\bMathTex\s*\(', 'Text(', code)
    code = re.sub(r'\bTex\s*\(', 'Text(', code)

    # Remove deprecated params
    for param in ['x_min', 'x_max', 'y_min', 'y_max']:
        code = re.sub(rf',\s*{param}\s*=[^,\)]+', '', code)
        code = re.sub(rf'{param}\s*=[^,\)]+,?\s*', '', code)

    logger.info(f"[ReelAgent] Generated Manim code: {len(code)} chars")
    return code


# ── Step 4: Render with Manim CE ──────────────────────────
def render_manim(code: str, job_id: str, work_dir: str, bg_color: str = "#1a1a2e") -> str:
    # Inject background color + vertical camera if not present
    if "self.camera.background_color" not in code:
        code = code.replace(
            "def construct(self):",
            f'def construct(self):\n        self.camera.background_color = "{bg_color}"',
        )

    scene_file = os.path.join(work_dir, f"scene_{job_id}.py")
    with open(scene_file, "w", encoding="utf-8") as f:
        f.write(code)

    logger.info(f"[ReelAgent] Rendering Manim scene: {scene_file}")

    media_dir = os.path.join(work_dir, "media").replace("\\", "/")

    # Render at 540x960 vertical, 30fps for smooth animation
    cmd = [
        sys.executable, "-m", "manim", "render",
        scene_file,
        "ReelScene",
        "-r", f"{RENDER_W},{RENDER_H}",
        "--fps", "30",
        "--format=mp4",
        f"--media_dir={media_dir}",
        "--disable_caching",
    ]

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=300, cwd=work_dir,
        )

        if result.returncode != 0:
            logger.error(f"[ReelAgent] Manim STDERR:\n{result.stderr[-1200:]}")
            fixed_code = _attempt_fix_manim(code, result.stderr)
            if fixed_code and fixed_code != code:
                logger.info("[ReelAgent] Attempting Manim code fix...")
                return render_manim(fixed_code, job_id + "_fix", work_dir, bg_color)
            return ""

        # Find the rendered MP4
        for root, dirs, files in os.walk(os.path.join(work_dir, "media")):
            for f in files:
                if f.endswith(".mp4") and "partial" not in root:
                    mp4_path = os.path.join(root, f)
                    logger.info(f"[ReelAgent] Rendered: {mp4_path} ({os.path.getsize(mp4_path) / 1024:.0f} KB)")
                    return mp4_path

        logger.error("[ReelAgent] No MP4 found after render")
        return ""

    except subprocess.TimeoutExpired:
        logger.error("[ReelAgent] Manim render timed out (5 min)")
        return ""
    except Exception as e:
        logger.error(f"[ReelAgent] Manim render exception: {e}")
        return ""


def _attempt_fix_manim(code: str, error: str) -> str:
    try:
        groq = _get_groq()
        resp = groq.chat.completions.create(
            model=GROQ_MODEL_PRIMARY,
            messages=[
                {"role": "system", "content": (
                    "Fix this Manim CE v0.20 code. Return ONLY corrected Python code.\n"
                    "Common fixes:\n"
                    "- MathTex->Text, Tex->Text (no LaTeX installed)\n"
                    "- remove x_min/x_max/y_min/y_max (use x_range/y_range)\n"
                    "- All coordinates MUST be 3D: np.array([x,y,0]) not [x,y]\n"
                    "- ParametricFunction lambda must return 3D: np.array([x,y,0])\n"
                    "- Ensure `from manim import *`, class ReelScene(Scene)\n"
                    "- Use .scale_to_fit_width(5.0) on all Text to prevent overflow"
                )},
                {"role": "user", "content": f"Code:\n{code}\n\nError:\n{error[-800:]}\n\nFix it."},
            ],
            max_tokens=4000,
            temperature=0.2,
        )
        fixed = resp.choices[0].message.content.strip()
        if fixed.startswith("```"):
            lines = fixed.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            fixed = "\n".join(lines)
        # Apply same safety fixes
        fixed = re.sub(r'\bMathTex\s*\(', 'Text(', fixed)
        fixed = re.sub(r'\bTex\s*\(', 'Text(', fixed)
        for param in ['x_min', 'x_max', 'y_min', 'y_max']:
            fixed = re.sub(rf',\s*{param}\s*=[^,\)]+', '', fixed)
            fixed = re.sub(rf'{param}\s*=[^,\)]+,?\s*', '', fixed)
        if "from manim import" in fixed and "class " in fixed:
            return fixed
    except Exception as e:
        logger.warning(f"[ReelAgent] Code fix failed: {e}")
    return ""


# ── Step 5: ElevenLabs TTS ────────────────────────────────
async def generate_voiceover(narration_text: str, output_path: str) -> str:
    """Generate TTS audio via Deepgram Aura-2 (Athena — natural female voice)."""
    if not DEEPGRAM_API_KEY:
        logger.warning("[ReelAgent] No Deepgram key - skipping TTS")
        return ""

    try:
        # Deepgram has a 2000 char limit per request
        text = narration_text[:1950]

        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                "https://api.deepgram.com/v1/speak?model=aura-2-athena-en&encoding=mp3",
                headers={
                    "Authorization": f"Token {DEEPGRAM_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={"text": text},
            )
            resp.raise_for_status()
            with open(output_path, "wb") as f:
                f.write(resp.content)

        logger.info(f"[ReelAgent] TTS (Deepgram): {len(resp.content)} bytes")
        return output_path
    except Exception as e:
        logger.warning(f"[ReelAgent] TTS failed (will publish without audio): {e}")
        return ""


# ── Step 6: FFmpeg — Merge + Upscale to Full Screen ───────
def assemble_reel(video_path: str, audio_path: str, output_path: str) -> str:
    """Merge Manim video + TTS audio. Speed-match video to audio for perfect sync."""
    has_audio = audio_path and os.path.exists(audio_path)

    # Get durations via ffprobe to sync video speed to audio
    def get_duration(path):
        try:
            probe = subprocess.run(
                ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
                 "-of", "csv=p=0", path],
                capture_output=True, text=True, timeout=10,
            )
            return float(probe.stdout.strip())
        except Exception:
            return 0.0

    vid_dur = get_duration(video_path)
    aud_dur = get_duration(audio_path) if has_audio else 0.0

    # Build video filter: upscale + speed adjustment to match audio
    filters = [f"scale={OUTPUT_W}:{OUTPUT_H}:flags=lanczos"]
    if has_audio and vid_dur > 0 and aud_dur > 0 and abs(vid_dur - aud_dur) > 1:
        # Speed up or slow down video to match audio duration
        speed_factor = vid_dur / aud_dur  # >1 means video is longer, speed it up
        # setpts divides by speed: PTS/speed_factor makes video faster when >1
        filters.append(f"setpts=PTS/{speed_factor:.4f}")
        logger.info(f"[ReelAgent] Sync: video={vid_dur:.1f}s audio={aud_dur:.1f}s speed={speed_factor:.2f}x")

    vf = ",".join(filters)

    cmd = ["ffmpeg", "-y", "-i", video_path]
    if has_audio:
        cmd.extend(["-i", audio_path])

    cmd.extend([
        "-vf", vf,
        "-c:v", "libx264", "-preset", "fast", "-crf", "23", "-pix_fmt", "yuv420p",
    ])
    if has_audio:
        cmd.extend(["-strict", "-2", "-c:a", "aac", "-shortest"])
    cmd.append(output_path)

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode != 0:
            logger.error(f"[ReelAgent] FFmpeg error: {result.stderr[-300:]}")
            return ""
        logger.info(f"[ReelAgent] Assembled: {output_path}")
        return output_path
    except Exception as e:
        logger.error(f"[ReelAgent] FFmpeg failed: {e}")
        return ""


def extract_thumbnail(video_path: str, output_path: str) -> str:
    cmd = [
        "ffmpeg", "-y", "-i", video_path,
        "-ss", "3", "-frames:v", "1",
        "-vf", f"scale={OUTPUT_W}:{OUTPUT_H}:flags=lanczos",
        output_path,
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0 and os.path.exists(output_path):
            return output_path
    except Exception:
        pass
    return ""


# ── Full Pipeline ─────────────────────────────────────────
async def run_reel_agent(domain: str) -> dict:
    reel_id = f"reel_{uuid.uuid4().hex[:12]}"
    logger.info(f"[ReelAgent] === START === domain={domain}, id={reel_id}")

    # Step 1: Research topic
    topic_data = await research_topic(domain)
    topic = topic_data["topic"]
    logger.info(f"[ReelAgent] Topic: {topic}")

    # Step 2: Plan video (story-based)
    plan = plan_video(topic, domain)
    narration_text = plan.get("narration", f"Let's explore {topic}.")
    # If narration came back as dict (old format), flatten it
    if isinstance(narration_text, dict):
        parts = [narration_text.get("hook", "")]
        parts.extend(narration_text.get("sections", []))
        parts.append(narration_text.get("cta", ""))
        narration_text = " ".join(p for p in parts if p)

    colors = plan.get("color_palette", {})
    bg_color = colors.get("background", "#1a1a2e")
    logger.info(f"[ReelAgent] Narration: {len(narration_text)} chars")

    # Step 3: Generate Manim code
    manim_code = generate_manim_code(plan)

    # Step 4 & 5 in parallel: Render Manim + Generate TTS
    tmp_dir = tempfile.mkdtemp(prefix="reel_manim_")
    audio_path = os.path.join(tmp_dir, "voiceover.mp3")

    manim_task = asyncio.get_event_loop().run_in_executor(
        None, render_manim, manim_code, reel_id, tmp_dir, bg_color
    )
    tts_task = generate_voiceover(narration_text, audio_path)

    manim_mp4, _ = await asyncio.gather(manim_task, tts_task, return_exceptions=False)

    if not manim_mp4:
        logger.error(f"[ReelAgent] Manim render failed for {reel_id}")
        return {
            "reel_id": reel_id, "domain": domain,
            "title": plan.get("title", topic), "script_text": narration_text,
            "s3_video_url": "", "s3_thumb_url": "",
            "source_type": "ai_generated", "content_type": "reel",
        }

    # Step 6: Assemble (upscale + merge audio)
    output_mp4 = os.path.join(tmp_dir, f"{reel_id}.mp4")
    has_audio = os.path.exists(audio_path) and os.path.getsize(audio_path) > 0
    assembled = assemble_reel(manim_mp4, audio_path if has_audio else "", output_mp4)

    # Step 7: Upload to S3
    s3_video_url = ""
    s3_thumb_url = ""
    final_mp4 = assembled if assembled else manim_mp4

    if final_mp4 and os.path.exists(final_mp4):
        size = os.path.getsize(final_mp4)
        logger.info(f"[ReelAgent] Final MP4: {size / 1024:.0f} KB")
        try:
            s3_video_url = upload_reel(final_mp4, domain, reel_id)
        except Exception as e:
            logger.error(f"[ReelAgent] S3 upload failed: {e}")

        thumb_path = os.path.join(tmp_dir, f"{reel_id}_thumb.jpg")
        if extract_thumbnail(final_mp4, thumb_path):
            try:
                with open(thumb_path, "rb") as f:
                    s3_thumb_url = upload_thumbnail(f.read(), domain, reel_id)
            except Exception as e:
                logger.error(f"[ReelAgent] Thumb upload failed: {e}")

    logger.info(f"[ReelAgent] === DONE === {reel_id} video={'YES' if s3_video_url else 'NO'}")

    return {
        "reel_id": reel_id, "domain": domain,
        "title": plan.get("title", topic), "script_text": narration_text,
        "s3_video_url": s3_video_url, "s3_thumb_url": s3_thumb_url,
        "source_type": "ai_generated", "content_type": "reel",
    }
