"""
interviewer.py
Core LLM logic:
  - generate_questions()  →  produce N role-specific interview questions
  - score_answer()        →  score a single answer 0-10 with feedback

Uses Groq with llama-3.3-70b-versatile for high-quality, fast responses.
All prompts are imported from prompts.py.
"""

import json
import os
import re
from groq import Groq
from dotenv import load_dotenv
from prompts import get_question_generator_prompt, get_scorer_prompt

load_dotenv()

# ── Groq client (singleton) ──────────────────────────────────────────────────
_client: Groq | None = None


def _get_client() -> Groq:
    global _client
    if _client is None:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise EnvironmentError(
                "GROQ_API_KEY not found.\n"
                "Set it in a .env file or export it as an environment variable."
            )
        _client = Groq(api_key=api_key)
    return _client


# ── Model config ─────────────────────────────────────────────────────────────
MODEL = "llama-3.3-70b-versatile"
TEMPERATURE_CREATIVE = 0.8   # for question generation (more varied)
TEMPERATURE_PRECISE = 0.2    # for scoring (consistent, deterministic)


# ── JSON extraction helper ────────────────────────────────────────────────────
def _extract_json(text: str) -> str:
    """
    Robustly extract the first JSON object or array from an LLM response.
    Handles cases where the model wraps JSON in markdown code fences.
    """
    # Strip markdown fences if present
    text = re.sub(r"```(?:json)?", "", text).strip()
    # Find the first { or [
    start = next((i for i, c in enumerate(text) if c in "{["), None)
    if start is None:
        raise ValueError(f"No JSON found in LLM response:\n{text}")
    return text[start:]


# ── Public API ────────────────────────────────────────────────────────────────

def generate_questions(role: str, skills: str, n: int = 6) -> list[str]:
    """
    Ask the LLM to generate n interview questions for the given role + skills.
    Returns a list of question strings.
    """
    client = _get_client()
    system_prompt = get_question_generator_prompt(role, skills, n)

    response = client.chat.completions.create(
        model=MODEL,
        temperature=TEMPERATURE_CREATIVE,
        messages=[
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": (
                    f"Generate {n} interview questions for a {role} "
                    f"candidate with skills: {skills}."
                ),
            },
        ],
    )

    raw = response.choices[0].message.content
    json_str = _extract_json(raw)
    questions = json.loads(json_str)

    if not isinstance(questions, list) or not questions:
        raise ValueError(f"Expected a JSON array of questions. Got:\n{raw}")

    return [str(q).strip() for q in questions[:n]]


def score_answer(role: str, question: str, answer: str) -> dict:
    """
    Score a single candidate answer.
    Returns dict: {"score": int, "feedback": str}
    """
    client = _get_client()

    if not answer.strip():
        return {"score": 0, "feedback": "No answer provided."}

    system_prompt = get_scorer_prompt(role, question, answer)

    response = client.chat.completions.create(
        model=MODEL,
        temperature=TEMPERATURE_PRECISE,
        messages=[
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": "Score the candidate's answer and return JSON.",
            },
        ],
    )

    raw = response.choices[0].message.content
    json_str = _extract_json(raw)
    result = json.loads(json_str)

    # Validate and clamp
    score = max(0, min(10, int(result.get("score", 0))))
    feedback = str(result.get("feedback", "No feedback provided.")).strip()

    return {"score": score, "feedback": feedback}
