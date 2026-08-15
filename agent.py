"""
agent.py
Entry point for the AI Interview Agent.

Supports two modes:
  1. New Session   — asks for role + skills, generates questions, runs full interview
  2. Resume Session — lists saved sessions, lets user pick one to continue

Run:
    python agent.py
"""

import sys
from utils import (
    console,
    print_welcome,
    print_section,
    print_goodbye,
    print_question,
    ask_answer,
    print_score,
    print_evaluation,
    print_sessions_table,
    prompt_input,
    prompt_choice,
    confirm,
    spinner,
)
from interviewer import generate_questions, score_answer
from evaluator import generate_evaluation
from storage import (
    list_sessions,
    load_session,
    save_session,
    export_csv,
    make_empty_session,
)


# ── Constants ─────────────────────────────────────────────────────────────────
DEFAULT_NUM_QUESTIONS = 6


# ── Session Runners ───────────────────────────────────────────────────────────

def run_new_session() -> None:
    """Collect role + skills, generate questions, run the full interview loop."""
    print_section("New Interview Session")

    role = prompt_input("Job role / title", "Software Engineer")
    skills = prompt_input(
        "Key skills to focus on (comma-separated)",
        "Python, REST APIs, SQL",
    )
    num_q = prompt_input(
        f"Number of questions",
        str(DEFAULT_NUM_QUESTIONS),
    )
    try:
        num_q = max(5, min(12, int(num_q)))
    except ValueError:
        num_q = DEFAULT_NUM_QUESTIONS

    session = make_empty_session(role, skills)

    # ── Generate questions ────────────────────────────────────────────────────
    console.print()
    with spinner(f"Generating {num_q} questions for [bold]{role}[/bold]…"):
        try:
            questions = generate_questions(role, skills, num_q)
        except Exception as e:
            console.print(f"\n[bold red]Error generating questions:[/bold red] {e}")
            sys.exit(1)

    session["questions"] = questions
    save_session(session)  # Save immediately so session survives interruption

    _run_interview_loop(session)


def run_resume_session() -> None:
    """List saved sessions and resume a chosen one from where it left off."""
    print_section("Resume a Saved Session")

    sessions = list_sessions()
    incomplete = [s for s in sessions if not s["has_evaluation"]]

    if not incomplete:
        console.print("[dim]No incomplete sessions to resume.[/dim]")
        console.print("[dim]All previous sessions are already complete.[/dim]\n")
        return

    print_sessions_table(incomplete)

    choices = [s["session_id"] for s in incomplete]
    session_id = prompt_choice("Select a session to resume", choices)

    session = load_session(session_id)
    if session is None:
        console.print(f"[red]Session '{session_id}' could not be loaded.[/red]")
        return

    answered = len(session.get("transcript", []))
    total = len(session.get("questions", []))
    console.print(
        f"\n[green]Resuming session[/green] [cyan]{session_id}[/cyan] "
        f"— [dim]{answered}/{total} questions answered so far[/dim]\n"
    )

    _run_interview_loop(session)


def _run_interview_loop(session: dict) -> None:
    """
    Core interview loop.
    Picks up from wherever the transcript left off (supports resume).
    """
    questions = session["questions"]
    transcript = session["transcript"]
    role = session["role"]
    skills = session["skills"]
    total = len(questions)

    # ── Determine starting point ──────────────────────────────────────────────
    answered_qs = {entry["question"] for entry in transcript}
    remaining = [q for q in questions if q not in answered_qs]

    if not remaining:
        console.print("[green]All questions already answered.[/green]")
        if not session.get("evaluation"):
            _finalize_session(session)
        return

    print_section("Interview in Progress")
    console.print(
        f"[dim]Role:[/dim] [bold]{role}[/bold]   "
        f"[dim]Skills:[/dim] {skills}   "
        f"[dim]Questions:[/dim] {total}\n"
    )

    for q in remaining:
        q_number = questions.index(q) + 1
        print_question(q_number, total, q)

        # ── Get candidate answer ──────────────────────────────────────────────
        answer = ask_answer(q_number)

        if not answer.strip():
            if not confirm("No answer entered. Skip this question?", default=False):
                # Re-prompt
                answer = ask_answer(q_number)

        # ── Score the answer ──────────────────────────────────────────────────
        with spinner("Evaluating your answer…"):
            try:
                result = score_answer(role, q, answer)
            except Exception as e:
                console.print(f"[red]Scoring error:[/red] {e}")
                result = {"score": 0, "feedback": "Could not evaluate (API error)."}

        print_score(result["score"], result["feedback"])

        # ── Save progress immediately ─────────────────────────────────────────
        transcript.append(
            {
                "question": q,
                "answer": answer,
                "score": result["score"],
                "feedback": result["feedback"],
            }
        )
        session["transcript"] = transcript
        save_session(session)

    # ── All questions done — finalize ─────────────────────────────────────────
    _finalize_session(session)


def _finalize_session(session: dict) -> None:
    """Generate final evaluation, print it, and save everything."""
    print_section("Generating Final Evaluation")

    with spinner("Analysing full transcript…"):
        try:
            evaluation = generate_evaluation(
                session["role"],
                session["skills"],
                session["transcript"],
            )
        except Exception as e:
            console.print(f"[red]Evaluation error:[/red] {e}")
            evaluation = {
                "overall_score": 0,
                "strengths": [],
                "gaps": ["Could not generate evaluation."],
                "hire_recommendation": "No",
                "recommendation_reason": str(e),
            }

    session["evaluation"] = evaluation
    json_path = save_session(session)
    csv_path = export_csv(session)

    print_evaluation(evaluation, session["role"])
    print_goodbye(str(json_path), str(csv_path))


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    print_welcome()

    saved = list_sessions()
    incomplete = [s for s in saved if not s["has_evaluation"]]

    mode_options = ["Start a new interview session"]
    if incomplete:
        mode_options.append(f"Resume a saved session ({len(incomplete)} incomplete)")
    mode_options.append("View all past sessions")
    mode_options.append("Exit")

    choice = prompt_choice("What would you like to do?", mode_options)

    if choice.startswith("Start"):
        run_new_session()

    elif choice.startswith("Resume"):
        run_resume_session()

    elif choice.startswith("View"):
        print_section("All Sessions")
        print_sessions_table(saved)
        # Ask if they want to resume one
        if saved and confirm("Resume or continue with any session?", default=False):
            run_resume_session()

    else:
        console.print("[dim]Goodbye! 👋[/dim]")
        sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n\n[yellow]Session interrupted. Your progress was auto-saved.[/yellow]")
        sys.exit(0)
