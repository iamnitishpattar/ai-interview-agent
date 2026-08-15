"""
evaluator.py
Generates the final hiring evaluation after all questions are answered.
Sends the full transcript to the LLM and parses the structured JSON response.
"""

import json
import os
import re
from groq import Groq
from dotenv import load_dotenv
from prompts import get_evaluator_prompt

load_dotenv()

MODEL = "llama-3.3-70b-versatile"


def _get_client() -> Groq:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise EnvironmentError("GROQ_API_KEY not set.")
    return Groq(api_key=api_key)


def _extract_json(text: str) -> str:
    """Strip markdown fences and extract the first JSON object."""
    text = re.sub(r"```(?:json)?", "", text).strip()
    start = next((i for i, c in enumerate(text) if c in "{["), None)
    if start is None:
        raise ValueError(f"No JSON found in evaluator response:\n{text}")
    return text[start:]


def generate_evaluation(role: str, skills: str, transcript: list[dict]) -> dict:
    """
    Generate a final hiring evaluation from the complete interview transcript.

    Parameters
    ----------
    role       : Job role (e.g. "Backend Developer")
    skills     : Comma-separated skills the candidate listed
    transcript : List of dicts with keys: question, answer, score, feedback

    Returns
    -------
    dict with keys:
        overall_score         (float)
        strengths             (list[str])
        gaps                  (list[str])
        hire_recommendation   (str)
        recommendation_reason (str)
    """
    if not transcript:
        return {
            "overall_score": 0.0,
            "strengths": [],
            "gaps": ["No answers were recorded."],
            "hire_recommendation": "No",
            "recommendation_reason": "The interview session contained no answers to evaluate.",
        }

    client = _get_client()
    system_prompt = get_evaluator_prompt(role, skills, transcript)

    response = client.chat.completions.create(
        model=MODEL,
        temperature=0.3,
        messages=[
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": "Generate the final hiring evaluation JSON.",
            },
        ],
    )

    raw = response.choices[0].message.content
    json_str = _extract_json(raw)
    result = json.loads(json_str)

    # Compute overall_score ourselves as a safety net
    scores = [entry["score"] for entry in transcript if isinstance(entry.get("score"), (int, float))]
    computed_avg = round(sum(scores) / len(scores), 1) if scores else 0.0

    return {
        "overall_score": result.get("overall_score", computed_avg),
        "strengths": result.get("strengths", []),
        "gaps": result.get("gaps", []),
        "hire_recommendation": result.get("hire_recommendation", "Maybe"),
        "recommendation_reason": result.get("recommendation_reason", ""),
    }
