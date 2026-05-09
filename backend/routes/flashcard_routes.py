"""
Flashcard API Routes — Generate study flashcards from any article/topic using Groq AI.
"""
import hashlib
import json
import logging
import asyncio
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from groq import Groq
from config import GROQ_API_KEY, GROQ_MODEL_PRIMARY
from auth import get_current_user
from cache import cache_get_json, cache_set_json

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/flashcards", tags=["Flashcards"])


class Flashcard(BaseModel):
    front: str
    back: str
    difficulty: str = "medium"


class FlashcardRequest(BaseModel):
    source: str  # article text, topic, or custom prompt
    count: int = 7
    topic: str = ""  # optional topic label


class FlashcardResponse(BaseModel):
    topic: str
    cards: List[Flashcard]


def _get_groq():
    return Groq(api_key=GROQ_API_KEY)


@router.post("/generate", response_model=FlashcardResponse)
async def generate_flashcards(req: FlashcardRequest, current_user: dict = Depends(get_current_user)):
    """Generate study flashcards from article/topic/text using Groq AI."""

    if not req.source or not req.source.strip():
        raise HTTPException(status_code=400, detail="Topic / source text is required")

    count = max(3, min(15, req.count))
    source_snippet = req.source[:4000]  # Cap input length

    # ── Cache: identical (source, count) hashes skip Groq entirely (24h TTL) ──
    cache_key = f"flash:{hashlib.sha256(f'{source_snippet}|{count}'.encode()).hexdigest()}"
    cached_payload = await cache_get_json(cache_key)
    if cached_payload:
        try:
            return FlashcardResponse(**cached_payload)
        except Exception:
            pass  # bad cache entry — recompute

    prompt = f"""Generate exactly {count} educational flashcards from this content:

{source_snippet}

REQUIREMENTS:
- Each flashcard has a FRONT (clear, specific question) and BACK (concise answer, max 2 sentences)
- Questions test understanding, not memorization of trivia
- Mix difficulty: include easy recall questions AND deeper "why/how" questions
- Make them sound like a real teacher's study cards
- Avoid yes/no questions — prefer "What is...", "Why does...", "How does...", "Explain..."
- Keep answers under 150 characters each
- Assign difficulty: easy, medium, or hard

Return ONLY valid JSON in this exact format:
{{
  "topic": "Brief 2-4 word topic label",
  "cards": [
    {{
      "front": "Question text?",
      "back": "Concise answer.",
      "difficulty": "easy|medium|hard"
    }}
  ]
}}"""

    try:
        groq = _get_groq()

        def _generate():
            resp = groq.chat.completions.create(
                model=GROQ_MODEL_PRIMARY,
                messages=[
                    {"role": "system", "content": "You are a skilled educator creating study flashcards. Generate clear, educational Q&A cards. Always return valid JSON only."},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=2000,
                temperature=0.7,
            )
            return resp.choices[0].message.content.strip()

        raw = await asyncio.to_thread(_generate)

        # Parse JSON — handle markdown code blocks
        cleaned = raw
        if "```" in cleaned:
            cleaned = cleaned.split("```")[1]
            if cleaned.startswith("json"):
                cleaned = cleaned[4:]
            cleaned = cleaned.strip()

        data = json.loads(cleaned)
        topic = data.get("topic") or req.topic or "Study Deck"
        cards_data = data.get("cards", [])

        # Validate
        valid_cards = []
        for c in cards_data:
            if isinstance(c.get("front"), str) and isinstance(c.get("back"), str):
                valid_cards.append(Flashcard(
                    front=c["front"].strip(),
                    back=c["back"].strip(),
                    difficulty=c.get("difficulty", "medium"),
                ))

        if len(valid_cards) < 2:
            raise ValueError("Not enough valid flashcards generated")

        result = FlashcardResponse(topic=topic, cards=valid_cards)
        # Cache for 24h — same input never re-hits Groq
        try:
            await cache_set_json(cache_key, result.model_dump(), ttl=24 * 60 * 60)
        except Exception:
            pass
        return result

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Groq flashcard JSON: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate flashcards. Try again.")
    except Exception as e:
        logger.error(f"Flashcard generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")
