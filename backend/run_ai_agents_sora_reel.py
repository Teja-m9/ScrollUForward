"""
AI Agents reel — Sora-2 AI video generation.
Run: python run_ai_agents_sora_reel.py
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
log = logging.getLogger("ai_agents_sora")

TOPIC   = "What Are AI Agents and How Do They Work?"
DOMAIN  = "ai"
REEL_ID = "reel_ai_agents_sora_001"

NARRATION = """
An AI agent isn't just a chatbot. It's a system that can perceive, reason, plan, and act — all on its own.

Think of it like this: a regular AI answers your question. An agent takes action. It can browse the web, write code, send emails, book meetings — without you pressing a button each time.

The secret is a four-step loop. First, Perception: the agent receives information from the world — text, images, tool results. Second, Reasoning: it uses a large language model to think through what it knows and what it needs. Third, Planning: it breaks big goals into small steps. Fourth, Action: it calls tools, APIs, or even other agents to get things done.

Memory makes agents truly powerful. Short-term memory holds the current conversation. Long-term memory stores facts across sessions — so an agent can remember your preferences tomorrow.

Multi-agent systems multiply this power. An orchestrator delegates tasks to specialist sub-agents — one searches the web, one writes the code, one checks the output. Like a team of experts, each doing what they do best.

This is the future of software: not apps you click through, but intelligent agents that work for you.

Follow ScrollUForward to learn something real every day.
"""


async def main():
    from agents.sora_reel_agent import generate_sora_reel

    log.info(f"Topic  : {TOPIC}")
    log.info(f"Domain : {DOMAIN}")
    log.info(f"Reel   : {REEL_ID}")
    log.info("Using Sora-2 for real AI video generation...")

    result = await generate_sora_reel(
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
