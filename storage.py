"""
storage.py
Handles saving and loading interview sessions as JSON.
Also exports a CSV summary for easy review.
"""

import json
import csv
import os
from datetime import datetime
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)


def _session_filename(session_id: str) -> Path:
    return OUTPUT_DIR / f"interview_{session_id}.json"


def generate_session_id() -> str:
    """Generate a unique session ID based on timestamp."""
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def save_session(session: dict) -> Path:
    """
    Save the full interview session to a JSON file.
    session must contain: session_id, role, skills, timestamp,
                          questions, transcript, evaluation (optional)
    Returns the path of the saved file.
    """
    path = _session_filename(session["session_id"])
    with open(path, "w", encoding="utf-8") as f:
        json.dump(session, f, indent=2, ensure_ascii=False)
    return path


def load_session(session_id: str) -> dict | None:
    """Load a saved session by its ID. Returns None if not found."""
    path = _session_filename(session_id)
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def list_sessions() -> list[dict]:
    """
    Return a list of all saved sessions with summary info.
    Each item: {session_id, role, skills, timestamp, questions_answered, has_evaluation}
    """
    sessions = []
    for fpath in sorted(OUTPUT_DIR.glob("interview_*.json"), reverse=True):
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                data = json.load(f)
            sessions.append(
                {
                    "session_id": data.get("session_id", "unknown"),
                    "role": data.get("role", "Unknown"),
                    "skills": data.get("skills", ""),
                    "timestamp": data.get("timestamp", ""),
                    "questions_answered": len(data.get("transcript", [])),
                    "total_questions": len(data.get("questions", [])),
                    "has_evaluation": "evaluation" in data and data["evaluation"] is not None,
                }
            )
        except (json.JSONDecodeError, KeyError):
            continue
    return sessions


def export_csv(session: dict) -> Path:
    """
    Export a completed session to a CSV file with one row per question.
    Returns the path of the CSV file.
    """
    csv_path = OUTPUT_DIR / f"interview_{session['session_id']}.csv"
    rows = []

    for i, entry in enumerate(session.get("transcript", []), 1):
        rows.append(
            {
                "session_id": session["session_id"],
                "role": session["role"],
                "skills": session["skills"],
                "question_number": i,
                "question": entry["question"],
                "answer": entry["answer"],
                "score": entry["score"],
                "feedback": entry["feedback"],
                "overall_score": session.get("evaluation", {}).get("overall_score", ""),
                "hire_recommendation": session.get("evaluation", {}).get("hire_recommendation", ""),
            }
        )

    if rows:
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)

    return csv_path


def make_empty_session(role: str, skills: str) -> dict:
    """Create a fresh session dict ready to be populated."""
    return {
        "session_id": generate_session_id(),
        "role": role,
        "skills": skills,
        "timestamp": datetime.now().isoformat(),
        "questions": [],
        "transcript": [],
        "evaluation": None,
    }
