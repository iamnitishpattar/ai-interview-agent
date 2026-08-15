"""
utils.py
Rich terminal UI helpers — panels, score bars, spinners, tables.
All display logic lives here so agent.py stays clean.
"""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.text import Text
from rich import box
from contextlib import contextmanager

console = Console()


# ──────────────────────────────────────────
# Banners & Headers
# ──────────────────────────────────────────

def print_welcome():
    banner = Text()
    banner.append("🎙  ", style="bold cyan")
    banner.append("AI Interview Agent", style="bold white")
    banner.append("  🎙", style="bold cyan")
    console.print(
        Panel(
            banner,
            subtitle="[dim]Powered by Groq · LLaMA 3.3 70B[/dim]",
            border_style="cyan",
            padding=(1, 4),
        )
    )
    console.print()


def print_section(title: str):
    console.rule(f"[bold cyan]{title}[/bold cyan]")
    console.print()


def print_goodbye(session_path: str, csv_path: str):
    console.print()
    console.print(
        Panel(
            f"[bold green]✅  Interview Complete![/bold green]\n\n"
            f"[dim]Results saved to:[/dim]\n"
            f"  📄 [cyan]{session_path}[/cyan]\n"
            f"  📊 [cyan]{csv_path}[/cyan]",
            border_style="green",
            padding=(1, 2),
        )
    )


# ──────────────────────────────────────────
# Questions & Answers
# ──────────────────────────────────────────

def print_question(number: int, total: int, question: str):
    console.print()
    console.print(
        Panel(
            f"[bold white]{question}[/bold white]",
            title=f"[cyan]Question {number} of {total}[/cyan]",
            border_style="blue",
            padding=(0, 2),
        )
    )


def ask_answer(number: int) -> str:
    console.print(f"[bold yellow]Your answer[/bold yellow] [dim](press Enter twice when done)[/dim]:")
    lines = []
    while True:
        line = input()
        if line == "" and lines and lines[-1] == "":
            break
        lines.append(line)
    # Strip trailing blank line added by double-enter
    while lines and lines[-1] == "":
        lines.pop()
    return "\n".join(lines).strip()


# ──────────────────────────────────────────
# Score Display
# ──────────────────────────────────────────

def _score_color(score: int) -> str:
    if score >= 8:
        return "bold green"
    elif score >= 5:
        return "bold yellow"
    else:
        return "bold red"


def _score_bar(score: int, max_score: int = 10) -> str:
    filled = round(score / max_score * 10)
    bar = "█" * filled + "░" * (10 - filled)
    return bar


def print_score(score: int, feedback: str):
    color = _score_color(score)
    bar = _score_bar(score)
    console.print()
    console.print(
        Panel(
            f"[{color}]{bar}  {score}/10[/{color}]\n\n"
            f"[dim]Feedback:[/dim] {feedback}",
            title="[bold]Evaluator's Verdict[/bold]",
            border_style="magenta",
            padding=(0, 2),
        )
    )
    console.print()


# ──────────────────────────────────────────
# Final Evaluation
# ──────────────────────────────────────────

def print_evaluation(evaluation: dict, role: str):
    overall = evaluation.get("overall_score", 0)
    rec = evaluation.get("hire_recommendation", "N/A")
    reason = evaluation.get("recommendation_reason", "")
    strengths = evaluation.get("strengths", [])
    gaps = evaluation.get("gaps", [])

    rec_color = {
        "Strong Yes": "bold green",
        "Yes": "green",
        "Maybe": "yellow",
        "No": "bold red",
    }.get(rec, "white")

    strengths_text = "\n".join(f"  [green]✔[/green] {s}" for s in strengths) or "  [dim]None noted[/dim]"
    gaps_text = "\n".join(f"  [red]✘[/red] {g}" for g in gaps) or "  [dim]None noted[/dim]"

    body = (
        f"[bold]Role:[/bold] {role}\n\n"
        f"[bold]Overall Score:[/bold] [{_score_color(int(overall))}]{overall}/10[/{_score_color(int(overall))}]  "
        f"{_score_bar(overall)}\n\n"
        f"[bold]Hire Recommendation:[/bold] [{rec_color}]{rec}[/{rec_color}]\n"
        f"[dim]{reason}[/dim]\n\n"
        f"[bold]Strengths[/bold]\n{strengths_text}\n\n"
        f"[bold]Gaps[/bold]\n{gaps_text}"
    )

    console.print()
    console.print(
        Panel(
            body,
            title="[bold cyan]📋  Final Evaluation[/bold cyan]",
            border_style="cyan",
            padding=(1, 2),
        )
    )


# ──────────────────────────────────────────
# Session List Table
# ──────────────────────────────────────────

def print_sessions_table(sessions: list[dict]) -> None:
    if not sessions:
        console.print("[dim]No saved sessions found.[/dim]\n")
        return

    table = Table(
        box=box.ROUNDED,
        border_style="cyan",
        title="[bold]📂  Saved Sessions[/bold]",
        show_lines=True,
    )
    table.add_column("#", style="dim", width=3)
    table.add_column("Session ID", style="cyan", no_wrap=True)
    table.add_column("Role", style="bold white")
    table.add_column("Skills", style="dim", max_width=30)
    table.add_column("Progress", justify="center")
    table.add_column("Evaluated", justify="center")

    for i, s in enumerate(sessions, 1):
        answered = s["questions_answered"]
        total = s["total_questions"]
        progress = f"{answered}/{total}" if total else f"{answered}/?"
        evaluated = "[green]✔[/green]" if s["has_evaluation"] else "[red]✘[/red]"
        table.add_row(str(i), s["session_id"], s["role"], s["skills"], progress, evaluated)

    console.print(table)
    console.print()


# ──────────────────────────────────────────
# Spinner context manager
# ──────────────────────────────────────────

@contextmanager
def spinner(message: str):
    """Context manager that shows a spinner while work is done."""
    with Progress(
        SpinnerColumn(style="cyan"),
        TextColumn(f"[cyan]{message}[/cyan]"),
        transient=True,
        console=console,
    ) as progress:
        progress.add_task("", total=None)
        yield


# ──────────────────────────────────────────
# Generic prompts
# ──────────────────────────────────────────

def prompt_input(label: str, default: str = "") -> str:
    """Prompt the user for text input with a styled label."""
    if default:
        console.print(f"[bold yellow]{label}[/bold yellow] [dim](default: {default})[/dim]: ", end="")
    else:
        console.print(f"[bold yellow]{label}[/bold yellow]: ", end="")
    value = input().strip()
    return value if value else default


def prompt_choice(label: str, choices: list[str]) -> str:
    """Present a numbered list and return the chosen item."""
    console.print(f"\n[bold yellow]{label}[/bold yellow]")
    for i, c in enumerate(choices, 1):
        console.print(f"  [cyan]{i}.[/cyan] {c}")
    while True:
        console.print(f"  Enter number [dim](1–{len(choices)})[/dim]: ", end="")
        raw = input().strip()
        if raw.isdigit() and 1 <= int(raw) <= len(choices):
            return choices[int(raw) - 1]
        console.print(f"  [red]Please enter a number between 1 and {len(choices)}.[/red]")


def confirm(label: str, default: bool = True) -> bool:
    """Yes/No confirmation prompt."""
    hint = "[Y/n]" if default else "[y/N]"
    console.print(f"[bold yellow]{label}[/bold yellow] {hint}: ", end="")
    raw = input().strip().lower()
    if raw == "":
        return default
    return raw in ("y", "yes")
