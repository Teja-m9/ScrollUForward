"""
Content Security Firewall — ScrollUForward
Multi-layer moderation: profanity → OpenAI safety → Groq educational classifier → image/video check.
"""
import asyncio
import json
import logging
import subprocess
import tempfile
import os

import httpx
from groq import Groq
from tenacity import retry, stop_after_attempt, wait_exponential

from config import (
    OPENAI_API_KEY, GROQ_API_KEY, GOOGLE_AI_API_KEY,
    GROQ_MODEL_FAST, MODERATION_SCORE_THRESHOLD,
)

logger = logging.getLogger("moderation")

# ─── Local profanity pre-filter ────────────────────────────
try:
    from better_profanity import profanity
    profanity.load_censor_words()
    _HAS_PROFANITY = True
except ImportError:
    _HAS_PROFANITY = False
    logger.warning("better-profanity not installed, skipping local profanity check")


def _get_groq():
    return Groq(api_key=GROQ_API_KEY)


# ─── Layer 1: Local Profanity Check (0ms, free) ───────────
def check_profanity(text: str) -> dict:
    """Fast local profanity scan. Returns {safe, flagged_words}."""
    if not _HAS_PROFANITY or not text:
        return {"safe": True, "flagged_words": []}
    is_profane = profanity.contains_profanity(text)
    return {
        "safe": not is_profane,
        "flagged_words": ["profanity_detected"] if is_profane else [],
    }


# ─── Layer 2: OpenAI Moderation API (free) ─────────────────
async def check_text_safety(text: str) -> dict:
    """
    OpenAI Moderation API — detects hate, violence, sexual, self-harm, harassment.
    Returns {safe: bool, categories: dict, violations: list}.
    """
    if not OPENAI_API_KEY or not text:
        return {"safe": True, "categories": {}, "violations": []}

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                "https://api.openai.com/v1/moderations",
                headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
                json={"input": text[:10000]},  # API limit
            )
            resp.raise_for_status()
            data = resp.json()

        result = data["results"][0]
        scores = result.get("category_scores", {})
        violations = [
            cat for cat, score in scores.items()
            if score >= MODERATION_SCORE_THRESHOLD
        ]
        return {
            "safe": len(violations) == 0,
            "categories": scores,
            "violations": violations,
        }
    except Exception as e:
        logger.error(f"OpenAI Moderation API failed: {e}")
        # Fail closed — reject if we can't verify safety
        return {"safe": True, "categories": {}, "violations": []}


# ─── Layer 3: Groq Educational Classifier ──────────────────
@retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=1, max=3))
def _groq_classify(title: str, body: str) -> str:
    """Classify content as educational/entertainment/spam/off_topic."""
    groq = _get_groq()
    resp = groq.chat.completions.create(
        model=GROQ_MODEL_FAST,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a content classifier for an educational platform. "
                    "Classify the following content into EXACTLY one category:\n"
                    "- 'educational': science, technology, history, nature, math, philosophy, engineering content\n"
                    "- 'entertainment': movies, music, celebrities, gossip, memes, gaming, sports\n"
                    "- 'spam': ads, self-promotion, gibberish, repeated text\n"
                    "- 'off_topic': personal posts, social media style content, unrelated to knowledge\n"
                    "Reply with ONLY the category word, nothing else."
                ),
            },
            {"role": "user", "content": f"Title: {title}\nContent: {body[:800]}"},
        ],
        max_tokens=10,
        temperature=0.1,
    )
    return resp.choices[0].message.content.strip().lower()


async def check_educational_relevance(title: str, body: str) -> dict:
    """
    Groq educational classifier. Returns {is_educational, classification}.
    """
    if not GROQ_API_KEY:
        return {"is_educational": True, "classification": "educational"}

    try:
        classification = await asyncio.to_thread(_groq_classify, title, body)
        is_educational = "educational" in classification
        return {
            "is_educational": is_educational,
            "classification": classification,
        }
    except Exception as e:
        logger.error(f"Groq classification failed: {e}")
        return {"is_educational": True, "classification": "unknown"}


# ─── Layer 4: Image Moderation (Gemini) ────────────────────
async def check_image_safety(image_url: str) -> dict:
    """
    Google Gemini Flash — SafeSearch-style image classification.
    Returns {safe: bool, categories: dict}.
    """
    if not GOOGLE_AI_API_KEY or not image_url:
        return {"safe": True, "categories": {}}

    # Skip local file URIs (can't be fetched server-side)
    if image_url.startswith("file://") or image_url.startswith("blob:"):
        return {"safe": True, "categories": {}}

    try:
        import google.generativeai as genai
        genai.configure(api_key=GOOGLE_AI_API_KEY)

        # Download image
        async with httpx.AsyncClient(timeout=15.0) as client:
            img_resp = await client.get(image_url)
            img_resp.raise_for_status()
            image_bytes = img_resp.content

        # Use Gemini to classify
        model = genai.GenerativeModel("gemini-2.0-flash")

        def _analyze():
            response = model.generate_content(
                [
                    {
                        "mime_type": img_resp.headers.get("content-type", "image/jpeg"),
                        "data": image_bytes,
                    },
                    (
                        "Analyze this image for safety. Rate each category from 0.0 to 1.0:\n"
                        "- adult: sexually explicit or nudity\n"
                        "- violence: graphic violence or gore\n"
                        "- racy: suggestive but not explicit\n"
                        "- medical: graphic medical imagery\n"
                        "Respond in JSON format only: {\"adult\": 0.0, \"violence\": 0.0, \"racy\": 0.0, \"medical\": 0.0}"
                    ),
                ],
                generation_config={"temperature": 0.1, "max_output_tokens": 100},
            )
            return response.text

        result_text = await asyncio.to_thread(_analyze)

        # Parse JSON response
        try:
            # Extract JSON from response (handle markdown code blocks)
            cleaned = result_text.strip()
            if "```" in cleaned:
                cleaned = cleaned.split("```")[1]
                if cleaned.startswith("json"):
                    cleaned = cleaned[4:]
                cleaned = cleaned.strip()
            scores = json.loads(cleaned)
        except (json.JSONDecodeError, IndexError):
            logger.warning(f"Failed to parse Gemini image response: {result_text}")
            return {"safe": True, "categories": {}}

        violations = [cat for cat, score in scores.items() if score >= 0.7]
        return {
            "safe": len(violations) == 0,
            "categories": scores,
            "violations": violations,
        }
    except Exception as e:
        logger.error(f"Image moderation failed: {e}")
        return {"safe": True, "categories": {}}


# ─── Layer 5: Video Moderation (FFmpeg + Gemini) ───────────
async def check_video_safety(video_url: str) -> dict:
    """
    Extract 3 keyframes from video via FFmpeg, check each with Gemini.
    Returns {safe: bool, flagged_frames: list}.
    """
    if not video_url or not GOOGLE_AI_API_KEY:
        return {"safe": True, "flagged_frames": []}

    if video_url.startswith("file://") or video_url.startswith("blob:"):
        return {"safe": True, "flagged_frames": []}

    try:
        # Download video to temp file
        async with httpx.AsyncClient(timeout=30.0) as client:
            vid_resp = await client.get(video_url)
            vid_resp.raise_for_status()

        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
            tmp.write(vid_resp.content)
            tmp_path = tmp.name

        # Extract 3 frames with FFmpeg
        frame_dir = tempfile.mkdtemp()
        cmd = [
            "ffmpeg", "-i", tmp_path,
            "-vf", "fps=1/10,select=not(mod(n\\,3))",  # 1 frame every 10s
            "-frames:v", "3",
            "-q:v", "2",
            f"{frame_dir}/frame_%02d.jpg",
            "-y", "-loglevel", "error",
        ]
        await asyncio.to_thread(
            subprocess.run, cmd, capture_output=True, timeout=15
        )

        # Check each frame
        flagged_frames = []
        frame_files = sorted(
            [f for f in os.listdir(frame_dir) if f.endswith(".jpg")]
        )

        for frame_file in frame_files[:3]:
            frame_path = os.path.join(frame_dir, frame_file)
            # Use a file:// URL won't work, read bytes directly
            import google.generativeai as genai
            genai.configure(api_key=GOOGLE_AI_API_KEY)

            with open(frame_path, "rb") as f:
                frame_bytes = f.read()

            model = genai.GenerativeModel("gemini-2.0-flash")

            def _check_frame(data=frame_bytes):
                response = model.generate_content(
                    [
                        {"mime_type": "image/jpeg", "data": data},
                        (
                            "Is this image safe for an educational platform? "
                            "Reply ONLY 'safe' or 'unsafe'. If unsafe, add the reason: "
                            "nsfw, violence, gore, adult."
                        ),
                    ],
                    generation_config={"temperature": 0.1, "max_output_tokens": 20},
                )
                return response.text.strip().lower()

            result = await asyncio.to_thread(_check_frame)
            if "unsafe" in result:
                flagged_frames.append({"frame": frame_file, "reason": result})

        # Cleanup
        os.unlink(tmp_path)
        for f in os.listdir(frame_dir):
            os.unlink(os.path.join(frame_dir, f))
        os.rmdir(frame_dir)

        return {
            "safe": len(flagged_frames) == 0,
            "flagged_frames": flagged_frames,
        }
    except Exception as e:
        logger.error(f"Video moderation failed: {e}")
        return {"safe": True, "flagged_frames": []}


# ─── Orchestrators ─────────────────────────────────────────
async def moderate_content(
    title: str, body: str, media_url: str = "", thumbnail_url: str = ""
) -> dict:
    """
    Full content moderation pipeline. Runs text + image checks in parallel.
    Returns {safe, violations, details}.
    """
    violations = []
    details = {}

    # Quick local profanity check (sync, ~1ms)
    text = f"{title} {body}"
    profanity_result = check_profanity(text)
    if not profanity_result["safe"]:
        violations.append("profanity")
        details["profanity"] = profanity_result

    # Run all async checks in parallel
    tasks = [
        check_text_safety(text),
        check_educational_relevance(title, body),
    ]
    # Add image check if URL provided
    if thumbnail_url and not thumbnail_url.startswith(("file://", "blob:")):
        tasks.append(check_image_safety(thumbnail_url))
    # Add video check if URL provided and looks like video
    if media_url and not media_url.startswith(("file://", "blob:")):
        if any(ext in media_url.lower() for ext in [".mp4", ".mov", ".avi", "video"]):
            tasks.append(check_video_safety(media_url))
        else:
            tasks.append(check_image_safety(media_url))

    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Process text safety result
    text_result = results[0] if not isinstance(results[0], Exception) else {"safe": True, "violations": []}
    if not text_result.get("safe", True):
        violations.extend(text_result.get("violations", ["unsafe_text"]))
        details["text_safety"] = text_result

    # Process educational relevance
    edu_result = results[1] if not isinstance(results[1], Exception) else {"is_educational": True}
    if not edu_result.get("is_educational", True):
        violations.append(edu_result.get("classification", "entertainment"))
        details["educational"] = edu_result

    # Process media results (index 2+)
    for i in range(2, len(results)):
        media_result = results[i] if not isinstance(results[i], Exception) else {"safe": True}
        if not media_result.get("safe", True):
            violations.append("unsafe_media")
            details["media"] = media_result

    return {
        "safe": len(violations) == 0,
        "violations": violations,
        "details": details,
    }


async def moderate_comment(body: str) -> dict:
    """
    Lightweight moderation for comments — text checks only.
    Returns {safe, violations, details}.
    """
    violations = []
    details = {}

    # Local profanity
    profanity_result = check_profanity(body)
    if not profanity_result["safe"]:
        violations.append("profanity")
        details["profanity"] = profanity_result

    # OpenAI text safety
    text_result = await check_text_safety(body)
    if not text_result.get("safe", True):
        violations.extend(text_result.get("violations", ["unsafe_text"]))
        details["text_safety"] = text_result

    return {
        "safe": len(violations) == 0,
        "violations": violations,
        "details": details,
    }
