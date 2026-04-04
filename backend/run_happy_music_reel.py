"""
Runner: Generate & push the "How Music Feels Happy" anime reel.
Run from backend/ directory:
    python run_happy_music_reel.py
"""
import asyncio
import logging
import sys
import os

# Ensure backend/ is on the path
sys.path.insert(0, os.path.dirname(__file__))

# Add KMPlayer FFmpeg to PATH
os.environ["PATH"] = r"C:\KMPlayer" + os.pathsep + os.environ.get("PATH", "")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)

TOPIC     = "How Music Makes You Feel Happy"
DOMAIN    = "arts"
REEL_ID   = "reel_happy_music_anime_004"
SCENE_FILE = "happy_music_reel.py"

BASE_NARRATION = """
Why does a song give you chills? Why do certain melodies make you smile instantly?
The answer is pure neuroscience. When music plays in a major key — those bright,
uplifting chords like C major — your auditory cortex signals safety and joy to
your limbic system. The pattern of intervals in major scales evolved to sound
like a human voice expressing happiness.

Then there's tempo. Music between 120 and 140 beats per minute synchronises with
your excited heartbeat, a phenomenon called entrainment. Your nervous system
literally aligns to the rhythm. That's why fast-paced songs make you want to
move — your body is syncing, not choosing to dance.

Bright timbres matter too. High-frequency overtones in instruments like the
trumpet or acoustic guitar activate more auditory nerve fibres, creating a
richer, more stimulating signal. Your ancient brain reads this as "alive,
energetic, safe."

And the reward? Pure dopamine. Neuroscientists at MIT discovered that happy music
triggers the same reward circuits as food, friendship, and love. Your brain
releases dopamine — the pleasure chemical — especially at musical moments you
predict AND at moments that surprise you. That tension and release is musical
happiness, engineered by evolution.

So the next time a song lifts your mood: that's not just feeling — that's your
neurons firing in a symphony of joy. Learn more on ScrollUForward!
"""


async def main():
    from agents.anime_reel_agent import generate_anime_reel

    logging.info("=== Starting Happy Music Anime Reel ===")
    logging.info(f"Topic   : {TOPIC}")
    logging.info(f"Domain  : {DOMAIN}")
    logging.info(f"Reel ID : {REEL_ID}")
    logging.info(f"Scene   : {SCENE_FILE}")

    result = await generate_anime_reel(
        manim_scene_file=SCENE_FILE,
        topic=TOPIC,
        domain=DOMAIN,
        original_narration=BASE_NARRATION.strip(),
        reel_id=REEL_ID,
    )

    print("\n" + "=" * 60)
    print("RESULT:")
    for k, v in result.items():
        if k != "script_text":
            print(f"  {k}: {v}")
    print("=" * 60)

    if result.get("status") == "published":
        print("\nREEL IS LIVE in the app feed!")
    elif result.get("s3_video_url"):
        print("\nReel uploaded to S3 - check Appwrite for publish status.")
    else:
        print("\nSomething failed - check logs above.")


if __name__ == "__main__":
    asyncio.run(main())
