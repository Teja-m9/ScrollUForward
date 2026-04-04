"""
AI Agents reel — Kurzgesagt-style illustrated video.
Run: python run_ai_agents_reel.py
"""
import asyncio
import logging
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
os.environ["PATH"] = r"C:\KMPlayer" + os.pathsep + os.environ.get("PATH", "")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
log = logging.getLogger("ai_agents_reel")

TOPIC   = "What Are AI Agents and How Do They Work?"
DOMAIN  = "ai"
REEL_ID = "reel_ai_agents_kurzgesagt_001"

NARRATION = """
An AI agent isn't just a chatbot. It's a system that can perceive, reason, plan, and act — all on its own.

Think of it like this: a regular AI answers questions. An agent takes actions. It can browse the web, write code, send emails, book a meeting — without you pressing a button each time.

The secret is a four-part loop. First, Perception: the agent receives information — text, images, tool results. Second, Reasoning: it uses a large language model to think about what it knows and what it needs. Third, Planning: it breaks big goals into smaller steps, deciding what to do next. Fourth, Action: it calls tools, APIs, or even other agents to make things happen.

Memory makes agents powerful. Short-term memory holds the current conversation. Long-term memory stores facts across sessions. This is how an agent can remember your preferences tomorrow.

Multi-agent systems take this further. One orchestrator agent delegates to specialist agents — a coder, a researcher, a reviewer — each doing what they do best.

This is the future of software: not apps you click through, but agents that act for you.

Learn more on ScrollUForward — where AI education comes alive.
"""


async def main():
    from agents.image_reel_agent import generate_image_reel

    log.info(f"Topic  : {TOPIC}")
    log.info(f"Domain : {DOMAIN}")
    log.info(f"Reel   : {REEL_ID}")

    result = await generate_image_reel(
        topic=TOPIC,
        domain=DOMAIN,
        narration=NARRATION.strip(),
        reel_id=REEL_ID,
    )

    print("\n" + "=" * 60)
    print(f"  ID     : {result.get('id', result.get('reel_id'))}")
    print(f"  Status : {result.get('status')}")
    print(f"  Video  : {'YES' if result.get('s3_video_url') else 'NO'}")
    print(f"  Audio  : {'YES' if result.get('has_audio') else 'NO'}")
    print(f"  Clips  : {result.get('clips_count', 0)}")
    print(f"  Thumb  : {'YES' if result.get('s3_thumb_url') else 'NO'}")
    print("=" * 60)

    if result.get("status") == "published":
        print("REEL IS LIVE in the app feed!")
    else:
        print(f"Error: {result.get('error', 'check logs')}")


if __name__ == "__main__":
    asyncio.run(main())
