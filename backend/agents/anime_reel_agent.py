"""
Anime × Manim Reel Pipeline
Generates educational reels with:
  - Manim animation as background
  - Anime character overlay (bottom-right)
  - Character-voiced narration (Deepgram TTS)
  - FFmpeg compositing
"""
import os, json, logging, subprocess, tempfile, httpx
from PIL import Image, ImageDraw, ImageFont
from openai import OpenAI

logger = logging.getLogger("scrolluforward")

# ── Original anime-style character archetypes (no copyrighted characters) ──
CHARACTER_MAP = {
    "mathematics": {
        "character": "Kaizen", "color": "#F39C12",
        "voice_style": "calm, strategic, sees patterns in everything",
        "dalle_prompt": (
            "An original anime male character named Kaizen, spiky dark grey hair, "
            "wearing a black hoodie with glowing gold circuit patterns, sharp intelligent eyes, "
            "holding a floating holographic equation, confident smirk, "
            "clean anime art style, full body portrait, dark background, vibrant colors, high detail"
        ),
    },
    "physics": {
        "character": "Ryoku", "color": "#E74C3C",
        "voice_style": "energetic, explosive enthusiasm, pure-hearted wonder",
        "dalle_prompt": (
            "An original anime male character named Ryoku, wild spiky orange hair, "
            "wearing a red and white training gi with energy aura effects, "
            "powerful confident stance, bright determined eyes, "
            "clean anime art style, full body portrait, dark background, vibrant colors, high detail"
        ),
    },
    "chemistry": {
        "character": "Mira", "color": "#16A085",
        "voice_style": "mysterious, intellectual, loves experiments",
        "dalle_prompt": (
            "An original anime female character named Mira, silver white hair with teal streaks, "
            "wearing a dark lab coat with glowing green vials attached, "
            "elegant and mysterious expression, holding a flask with colorful liquid, "
            "clean anime art style, full body portrait, dark background, vibrant colors, high detail"
        ),
    },
    "biology": {
        "character": "Chibi Doc", "color": "#27AE60",
        "voice_style": "adorable, excited about every living thing, enthusiastic learner",
        "dalle_prompt": (
            "An original cute chibi anime character named Chibi Doc, big round eyes, "
            "small fluffy brown hair with a tiny doctor hat, wearing a white medical coat "
            "with a green heart patch, holding a stethoscope, cheerful and curious expression, "
            "clean anime art style, full body portrait, dark background, vibrant colors, high detail"
        ),
    },
    "history": {
        "character": "Sage", "color": "#D4A843",
        "voice_style": "wise, philosophical, speaks as if they witnessed everything",
        "dalle_prompt": (
            "An original anime elder character named Sage, long white wavy hair, "
            "wearing an ancient golden scholar's robe with historical symbols, "
            "calm wise expression, holding an old glowing scroll, "
            "clean anime art style, full body portrait, dark background, vibrant colors, high detail"
        ),
    },
    "space": {
        "character": "Nova", "color": "#1ABC9C",
        "voice_style": "brilliant, scientific, always excited about the cosmos",
        "dalle_prompt": (
            "An original anime female character named Nova, short teal hair with star clips, "
            "wearing a sleek white and blue space explorer suit with constellation patterns, "
            "bright curious eyes, holding a small glowing planet model, "
            "clean anime art style, full body portrait, dark background, vibrant colors, high detail"
        ),
    },
    "technology": {
        "character": "Sora", "color": "#1976D2",
        "voice_style": "cool, precise, elite, speaks in efficient bursts",
        "dalle_prompt": (
            "An original anime male character named Sora, dark blue spiky hair, "
            "wearing a futuristic dark tech suit with glowing blue circuits, "
            "cool composed expression, one hand gesturing with digital data streams, "
            "clean anime art style, full body portrait, dark background, vibrant colors, high detail"
        ),
    },
    "ai": {
        "character": "Sora", "color": "#ED4956",
        "voice_style": "cool, precise, elite, speaks in efficient bursts",
        "dalle_prompt": (
            "An original anime male character named Sora, dark blue spiky hair, "
            "wearing a futuristic dark tech suit with glowing blue circuits, "
            "cool composed expression, one hand gesturing with digital data streams, "
            "clean anime art style, full body portrait, dark background, vibrant colors, high detail"
        ),
    },
    "nature": {
        "character": "Fern", "color": "#2ECC71",
        "voice_style": "smart, confident, deeply connected to the natural world",
        "dalle_prompt": (
            "An original anime female character named Fern, flowing green hair with flowers woven in, "
            "wearing a nature explorer vest with leaf patterns, bright green eyes, "
            "confident smile, surrounded by floating leaves and petals, "
            "clean anime art style, full body portrait, dark background, vibrant colors, high detail"
        ),
    },
    "psychology": {
        "character": "Zen", "color": "#8E44AD",
        "voice_style": "deep, wise, philosophical, calm authority",
        "dalle_prompt": (
            "An original anime male character named Zen, dark hair with a streak of purple, "
            "wearing a deep purple meditative robe with eye symbols, "
            "calm and piercing gaze, hands folded in a thoughtful pose, "
            "clean anime art style, full body portrait, dark background, vibrant colors, high detail"
        ),
    },
    "arts": {
        "character": "Blaze", "color": "#E67E22",
        "voice_style": "enthusiastic, creative, bursting with energy and passion",
        "dalle_prompt": (
            "An original anime male character named Blaze, wild spiky golden yellow hair, "
            "wearing a bright orange and white hoodie with music note patterns, "
            "huge energetic grin, one fist raised in excitement, "
            "clean anime art style, full body portrait, dark background, vibrant colors, high detail"
        ),
    },
    "literature": {
        "character": "Aria", "color": "#9B59B6",
        "voice_style": "calm, scholarly, elegant, speaks with poetic precision",
        "dalle_prompt": (
            "An original anime female character named Aria, long dark purple flowing hair, "
            "wearing an elegant dark academic dress with book motifs, "
            "calm intelligent expression, holding an open glowing book, "
            "clean anime art style, full body portrait, dark background, vibrant colors, high detail"
        ),
    },
    "economics": {
        "character": "Coin", "color": "#F39C12",
        "voice_style": "sharp, money-savvy, strategic and witty",
        "dalle_prompt": (
            "An original anime female character named Coin, short orange hair, "
            "wearing a sharp business blazer with golden coin motifs, "
            "clever confident smirk, holding a glowing coin, "
            "clean anime art style, full body portrait, dark background, vibrant colors, high detail"
        ),
    },
}


def get_character_for_domain(domain: str) -> dict:
    return CHARACTER_MAP.get(domain, CHARACTER_MAP["technology"])


def generate_character_image(character_name: str, anime: str, domain: str, output_path: str) -> str:
    """Generate original anime-style character image using DALL-E 3."""
    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        logger.warning("[AnimeReel] No OpenAI key, using fallback card")
        return _create_fallback_card(character_name, domain, output_path)

    char_info = get_character_for_domain(domain)
    dalle_prompt = char_info.get("dalle_prompt", (
        f"An original anime character named {character_name}, "
        f"standing pose, explaining something with one hand raised, "
        f"clean anime art style, vibrant colors, dark background, "
        f"full body shot, high quality anime illustration"
    ))

    try:
        client = OpenAI(api_key=api_key)

        response = client.images.generate(
            model="dall-e-3",
            prompt=dalle_prompt,
            size="1024x1792",
            quality="standard",
            n=1,
        )

        image_url = response.data[0].url
        # Download the image
        img_data = httpx.get(image_url, timeout=30).content
        with open(output_path, "wb") as f:
            f.write(img_data)

        # Resize to fit bottom-right overlay area (480x600 pixels)
        img = Image.open(output_path)
        img = img.resize((480, 600), Image.LANCZOS)
        img.save(output_path)

        logger.info(f"[AnimeReel] Character image generated: {character_name}")
        return output_path

    except Exception as e:
        logger.error(f"[AnimeReel] DALL-E failed: {e}, using fallback")
        return _create_fallback_card(character_name, domain, output_path)


def _create_fallback_card(character_name: str, domain: str, output_path: str) -> str:
    """Create a styled character card as fallback when DALL-E isn't available."""
    char_info = get_character_for_domain(domain)
    color = char_info["color"]

    # Parse hex color
    r, g, b = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)

    img = Image.new("RGBA", (480, 600), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Semi-transparent card background
    draw.rounded_rectangle([(20, 20), (460, 580)], radius=30,
                           fill=(r, g, b, 40), outline=(r, g, b, 180), width=3)

    # Character initial circle
    cx, cy = 240, 200
    draw.ellipse([(cx-80, cy-80), (cx+80, cy+80)], fill=(r, g, b, 100), outline=(r, g, b, 220), width=4)

    # Character initial
    try:
        font_large = ImageFont.truetype("arial.ttf", 80)
        font_name = ImageFont.truetype("arial.ttf", 32)
        font_anime = ImageFont.truetype("arial.ttf", 22)
        font_label = ImageFont.truetype("arial.ttf", 18)
    except Exception:
        font_large = ImageFont.load_default()
        font_name = font_large
        font_anime = font_large
        font_label = font_large

    initial = character_name[0]
    draw.text((cx, cy), initial, fill=(255, 255, 255, 255), font=font_large, anchor="mm")

    # Character name
    draw.text((240, 340), character_name, fill=(255, 255, 255, 240), font=font_name, anchor="mm")

    # Anime series
    anime_name = char_info.get("character", domain)
    draw.text((240, 385), anime_name, fill=(r, g, b, 200), font=font_anime, anchor="mm")

    # "Explaining" label
    draw.text((240, 450), "is explaining...", fill=(200, 200, 200, 180), font=font_label, anchor="mm")

    # Domain badge
    draw.rounded_rectangle([(140, 480), (340, 520)], radius=15,
                           fill=(r, g, b, 150), outline=(r, g, b, 200), width=2)
    draw.text((240, 500), domain.upper(), fill=(255, 255, 255, 255), font=font_label, anchor="mm")

    img.save(output_path, "PNG")
    logger.info(f"[AnimeReel] Fallback card created: {character_name}")
    return output_path


def generate_character_script(topic: str, domain: str, narration: str) -> str:
    """Re-voice the narration in the character's personality using Groq."""
    char_info = get_character_for_domain(domain)
    character = char_info["character"]
    voice_style = char_info["voice_style"]

    try:
        from groq import Groq
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": (
                    f"You are {character}, an original anime-style educational character. "
                    f"Your voice style: {voice_style}. "
                    f"Rewrite the following educational narration in your authentic character voice. "
                    f"Keep ALL the educational facts and content intact. "
                    f"Add character personality, catchphrases, and speaking style. "
                    f"Keep it 60-90 seconds when read aloud. "
                    f"End with: 'Learn more on ScrollUForward!' "
                    f"Output ONLY the narration text, no stage directions."
                )},
                {"role": "user", "content": f"Topic: {topic}\nDomain: {domain}\n\nOriginal narration:\n{narration}"}
            ],
            temperature=0.8,
            max_tokens=800,
        )

        script = response.choices[0].message.content.strip()
        logger.info(f"[AnimeReel] Character script generated: {character} ({len(script)} chars)")
        return script

    except Exception as e:
        logger.error(f"[AnimeReel] Script gen failed: {e}, using original")
        return narration


def composite_anime_reel(
    manim_video: str,
    character_image: str,
    audio_path: str,
    output_path: str,
) -> str:
    """Composite: Manim background + character overlay (bottom-right) + audio."""

    # Get video and audio durations for sync
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

    vid_dur = get_duration(manim_video)
    aud_dur = get_duration(audio_path) if audio_path and os.path.exists(audio_path) else 0.0
    has_audio = aud_dur > 0

    # Build video filter: upscale + speed match + character overlay
    filters = []

    # Speed match video to audio
    if has_audio and vid_dur > 0 and aud_dur > 0 and abs(vid_dur - aud_dur) > 1:
        speed = vid_dur / aud_dur
        filters.append(f"setpts=PTS/{speed:.4f}")
        logger.info(f"[AnimeReel] Sync: video={vid_dur:.1f}s audio={aud_dur:.1f}s speed={speed:.2f}x")

    # Scale to 1080x1920
    filters.append("scale=1080:1920:flags=lanczos")

    vf = ",".join(filters) if filters else "scale=1080:1920:flags=lanczos"

    # Build FFmpeg command with character overlay
    cmd = [
        "ffmpeg", "-y",
        "-i", manim_video,
        "-i", character_image,
    ]
    if has_audio:
        cmd.extend(["-i", audio_path])

    # Complex filter: scale video, then overlay character at bottom-right
    filter_complex = (
        f"[0:v]{vf}[bg];"
        f"[1:v]format=rgba,scale=350:-1[char];"
        f"[bg][char]overlay=W-w-20:H-h-120[vout]"
    )

    cmd.extend([
        "-filter_complex", filter_complex,
        "-map", "[vout]",
    ])
    if has_audio:
        cmd.extend(["-map", "2:a", "-strict", "-2", "-c:a", "aac", "-shortest"])

    cmd.extend([
        "-c:v", "libx264", "-preset", "fast", "-crf", "23", "-pix_fmt", "yuv420p",
        output_path
    ])

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode != 0:
            logger.error(f"[AnimeReel] FFmpeg error: {result.stderr[-400:]}")
            return ""
        logger.info(f"[AnimeReel] Composited: {output_path}")
        return output_path
    except Exception as e:
        logger.error(f"[AnimeReel] FFmpeg failed: {e}")
        return ""


async def generate_anime_reel(
    manim_scene_file: str,
    topic: str,
    domain: str,
    original_narration: str,
    reel_id: str,
) -> dict:
    """Full pipeline: render Manim → generate character image → character script → TTS → composite."""
    from agents.reel_agent import generate_voiceover, extract_thumbnail
    from agents.domain_router import publish_reel
    from s3_client import upload_reel, upload_thumbnail as upload_thumb

    tmp_dir = tempfile.mkdtemp(prefix=f"anime_reel_{domain}_")
    char_info = get_character_for_domain(domain)

    logger.info(f"[AnimeReel] Starting: {topic} | Character: {char_info['character']}")

    # 1. Render Manim scene
    import sys
    scenes_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "scenes")
    scene_path = os.path.join(scenes_dir, manim_scene_file)
    media_dir = os.path.join(tmp_dir, "media")

    render_cmd = [
        sys.executable, "-m", "manim", "render",
        scene_path, "ReelScene",
        "-r", "540,960", "--fps", "30", "--format=mp4",
        f"--media_dir={media_dir}", "--disable_caching",
    ]
    render_result = subprocess.run(render_cmd, capture_output=True, text=True, timeout=300)
    if render_result.returncode != 0:
        logger.error(f"[AnimeReel] Manim render failed")
        return {}

    # Find the MP4
    manim_mp4 = ""
    for root, dirs, files in os.walk(media_dir):
        for f in files:
            if f.endswith(".mp4") and "partial" not in root:
                manim_mp4 = os.path.join(root, f)
                break
        if manim_mp4:
            break

    if not manim_mp4:
        return {}
    logger.info(f"[AnimeReel] Manim rendered: {os.path.getsize(manim_mp4) / 1024:.0f} KB")

    # 2. Generate character image
    char_img_path = os.path.join(tmp_dir, "character.png")
    generate_character_image(char_info["character"], "", domain, char_img_path)

    # 3. Generate character-voiced script
    char_script = generate_character_script(topic, domain, original_narration)

    # 4. TTS with Deepgram
    audio_path = os.path.join(tmp_dir, "voiceover.mp3")
    await generate_voiceover(char_script, audio_path)
    has_audio = os.path.exists(audio_path) and os.path.getsize(audio_path) > 0

    # 5. Composite: Manim + character overlay + audio
    output_mp4 = os.path.join(tmp_dir, f"{reel_id}.mp4")
    final = composite_anime_reel(
        manim_mp4,
        char_img_path,
        audio_path if has_audio else "",
        output_mp4
    )
    if not final:
        final = manim_mp4

    logger.info(f"[AnimeReel] Final: {os.path.getsize(final) / 1024:.0f} KB")

    # 6. Upload to S3
    s3_url = upload_reel(final, domain, reel_id)
    s3_thumb = ""
    thumb_path = os.path.join(tmp_dir, f"{reel_id}_thumb.jpg")
    if extract_thumbnail(final, thumb_path):
        with open(thumb_path, "rb") as f:
            s3_thumb = upload_thumb(f.read(), domain, reel_id)

    # 7. Publish to Appwrite
    pub = publish_reel({
        "reel_id": reel_id,
        "domain": domain,
        "title": f"{char_info['character']} explains: {topic}",
        "script_text": char_script,
        "s3_video_url": s3_url,
        "s3_thumb_url": s3_thumb,
        "source_type": "ai_generated",
        "content_type": "reel",
    })

    logger.info(f"[AnimeReel] Published: {reel_id} | {char_info['character']} → {domain}")
    return pub
