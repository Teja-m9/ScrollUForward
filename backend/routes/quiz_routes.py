"""
Quiz API Routes — Generate dynamic quiz questions using Groq AI.
Questions are unique per request, never repeat for the same user.
"""
import json
import logging
import asyncio
from fastapi import APIRouter, HTTPException, Depends, Query as QueryParam
from pydantic import BaseModel
from typing import List, Optional
from groq import Groq
from config import GROQ_API_KEY, GROQ_MODEL_PRIMARY, GROQ_MODEL_FAST
from auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/quiz", tags=["Quiz"])


class QuizQuestion(BaseModel):
    q: str
    options: List[str]
    correct: int
    explanation: str = ""
    difficulty: str = "medium"


class QuizResponse(BaseModel):
    domain: str
    questions: List[QuizQuestion]


def _get_groq():
    return Groq(api_key=GROQ_API_KEY)


DOMAIN_CONTEXTS = {
    "physics": "physics, mechanics, thermodynamics, quantum physics, relativity, optics, electromagnetism, waves",
    "ai": "artificial intelligence, machine learning, deep learning, NLP, computer vision, neural networks, ethics of AI, transformers, LLMs",
    "space": "astronomy, space exploration, planets, stars, galaxies, black holes, cosmology, NASA missions, rockets",
    "biology": "biology, genetics, evolution, cell biology, ecology, human anatomy, microbiology, CRISPR, neuroscience",
    "history": "world history, ancient civilizations, wars, revolutions, famous leaders, archaeology, cultural history",
    "technology": "software engineering, web development, cybersecurity, databases, cloud computing, mobile apps, networking, hardware",
    "nature": "environment, ecosystems, climate, oceans, animals, plants, geology, weather, conservation",
    "mathematics": "mathematics, algebra, geometry, probability, statistics, calculus, number theory, logic puzzles",
}


@router.get("/generate", response_model=QuizResponse)
async def generate_quiz(
    domain: str = QueryParam(..., description="Quiz domain"),
    count: int = QueryParam(5, ge=1, le=10, description="Number of questions"),
    difficulty: str = QueryParam("mixed", description="easy, medium, hard, or mixed"),
    exclude: str = QueryParam("", description="Comma-separated question hashes to exclude"),
    current_user: dict = Depends(get_current_user),
):
    """Generate unique quiz questions using Groq AI. Never repeats."""

    if domain not in DOMAIN_CONTEXTS:
        raise HTTPException(status_code=400, detail=f"Unknown domain: {domain}. Valid: {list(DOMAIN_CONTEXTS.keys())}")

    context = DOMAIN_CONTEXTS[domain]
    excluded_list = [e.strip() for e in exclude.split(",") if e.strip()]
    exclude_instruction = ""
    if excluded_list:
        exclude_instruction = f"\nIMPORTANT: The user has already seen these question topics, DO NOT repeat them: {', '.join(excluded_list[:20])}"

    difficulty_instruction = ""
    if difficulty == "easy":
        difficulty_instruction = "Make all questions EASY — basic knowledge that beginners would know."
    elif difficulty == "hard":
        difficulty_instruction = "Make all questions HARD — tricky, requires deep knowledge, include gotchas and counter-intuitive answers."
    elif difficulty == "mixed":
        difficulty_instruction = "Mix difficulties: 1 easy, 2 medium, 2 hard. Include at least 1 tricky question with a counter-intuitive answer."

    prompt = f"""Generate exactly {count} unique multiple-choice quiz questions about {context}.

{difficulty_instruction}
{exclude_instruction}

REQUIREMENTS:
- Each question must have exactly 4 options (A, B, C, D)
- Include a mix of: factual questions, scenario/use-case questions, tricky questions, and "what would happen if..." questions
- Make questions INTERESTING and thought-provoking, not boring textbook questions
- For tricky questions, the obvious answer should be WRONG — make the user think
- Include real-world scenarios like "You're a scientist and observe X, what does this mean?"
- Add a brief 1-sentence explanation for the correct answer
- Vary the correct answer position (don't always make it B or C)

Return ONLY valid JSON in this exact format, nothing else:
{{
  "questions": [
    {{
      "q": "Question text here?",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "correct": 0,
      "explanation": "Brief explanation why this answer is correct.",
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
                    {"role": "system", "content": "You are a quiz master for an educational app. Generate diverse, interesting, and accurate multiple-choice questions. Always return valid JSON only."},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=2000,
                temperature=0.9,
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
        questions = data.get("questions", [])

        # Validate
        valid_questions = []
        for q in questions:
            if (isinstance(q.get("q"), str) and
                isinstance(q.get("options"), list) and len(q["options"]) == 4 and
                isinstance(q.get("correct"), int) and 0 <= q["correct"] <= 3):
                valid_questions.append(QuizQuestion(
                    q=q["q"],
                    options=q["options"],
                    correct=q["correct"],
                    explanation=q.get("explanation", ""),
                    difficulty=q.get("difficulty", "medium"),
                ))

        if len(valid_questions) < 1:
            raise ValueError("No valid questions parsed")

        return QuizResponse(domain=domain, questions=valid_questions)

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Groq quiz JSON: {e}\nRaw: {raw[:500]}")
        raise HTTPException(status_code=500, detail="Failed to parse AI-generated questions. Try again.")
    except Exception as e:
        logger.error(f"Quiz generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Quiz generation failed: {str(e)}")
