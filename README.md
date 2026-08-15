# 🎙 AI Interview Agent

A command-line AI agent that conducts **structured, role-specific technical interviews**, scores each answer in real-time, and produces a final hiring evaluation — all powered by **Groq** (free, fast LLaMA 3.3 70B).

---

## Demo

```
> python agent.py

╭──────────────────────────────────╮
│  🎙  AI Interview Agent  🎙      │
│  Powered by Groq · LLaMA 3.3 70B │
╰──────────────────────────────────╯

What would you like to do?
  1. Start a new interview session
  2. Resume a saved session (1 incomplete)
  3. View all past sessions
  4. Exit
```

---

## Features

| Feature | Details |
|---------|---------|
| 🎯 Role-aware questions | Generates 5–12 tailored questions from role + skills |
| 📊 Live scoring | Every answer scored 0–10 with one-line feedback |
| 💾 Auto-save | Progress saved after every answer — never lose work |
| 🔄 Resume sessions | Continue any incomplete session from where you left off |
| 📋 Final evaluation | Overall score, strengths, gaps, hire recommendation |
| 📁 Output files | JSON (full transcript) + CSV (spreadsheet-ready) |
| 🎨 Rich terminal UI | Colored panels, score bars, progress spinners |

---

## Prerequisites

- Python 3.10 or higher
- A free [Groq API key](https://console.groq.com) (takes 2 minutes to get)

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/your-username/interview-agent.git
cd interview-agent
```

### 2. Create a virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure your API key

```bash
# Copy the example file
cp .env.example .env      # macOS/Linux
copy .env.example .env    # Windows
```

Open `.env` and paste your Groq API key:

```
GROQ_API_KEY=gsk_your_actual_key_here
```

Get your free key at → https://console.groq.com

---

## Running the Agent

```bash
python agent.py
```

You'll be shown a menu:

```
1. Start a new interview session
2. Resume a saved session
3. View all past sessions
4. Exit
```

### Starting a new session

1. Select option **1**
2. Enter the **job role** (e.g. `Backend Developer`)
3. Enter **key skills** to focus on (e.g. `Python, FastAPI, PostgreSQL, Docker`)
4. Enter the **number of questions** (5–12, default 6)
5. Answer each question — press **Enter twice** when done
6. View your score after each answer
7. Receive a full evaluation at the end

### Resuming a session

1. Select option **2**
2. Pick from the list of incomplete sessions
3. Continue from the last unanswered question

---

## Output Files

All output is saved to the `output/` folder automatically.

| File | Contents |
|------|----------|
| `output/interview_<timestamp>.json` | Full session: questions, answers, scores, evaluation |
| `output/interview_<timestamp>.csv` | One row per question — easy to open in Excel/Sheets |

### Example JSON structure

```json
{
  "session_id": "20260815_100000",
  "role": "Backend Developer",
  "skills": "Python, FastAPI, PostgreSQL",
  "transcript": [
    {
      "question": "Explain async vs sync in Python...",
      "answer": "Async allows non-blocking I/O...",
      "score": 9,
      "feedback": "Excellent — correctly distinguishes I/O vs CPU-bound."
    }
  ],
  "evaluation": {
    "overall_score": 8.7,
    "strengths": ["Deep Python knowledge", "Production-level API design"],
    "gaps": ["No mention of observability"],
    "hire_recommendation": "Strong Yes",
    "recommendation_reason": "..."
  }
}
```

---

## Sample Transcripts

A complete pre-run interview transcript is included:

```
sample_transcripts/
└── backend_dev_interview.json   ← Full 6-question Backend Developer session
```

Open it to see the expected output format before running your own session.

---

## Scoring Method

Each answer is scored **0–10** by LLaMA 3.3 70B using this rubric:

| Score | Meaning |
|-------|---------|
| 0–3 | Incorrect, vague, off-topic, or no answer |
| 4–6 | Partially correct — missing key concepts or depth |
| 7–8 | Correct with good depth and relevant points |
| 9–10 | Excellent — thorough, precise, demonstrates mastery |

The **overall score** is the arithmetic mean of all question scores, rounded to 1 decimal.

### Why LLM-based scoring?

Traditional NLP scoring (keyword matching, TF-IDF) is brittle for open-ended technical answers. An LLM can:
- Understand paraphrasing and synonyms
- Recognize conceptual correctness even with different wording
- Reward examples and nuance, not just keyword presence

The scorer prompt uses `temperature=0.2` (near-deterministic) to ensure consistent, repeatable scores for the same answer.

---

## Project Structure

```
interview-agent/
├── agent.py                    ← Main entry point (CLI loop)
├── interviewer.py              ← LLM: question generation + answer scoring
├── evaluator.py                ← LLM: final hiring evaluation
├── prompts.py                  ← All system prompts (separated for easy tuning)
├── storage.py                  ← JSON/CSV save + load + session list
├── utils.py                    ← Rich terminal UI helpers
├── sample_transcripts/
│   └── backend_dev_interview.json
├── output/                     ← Auto-created; stores your sessions
├── .env.example                ← API key template
├── requirements.txt
└── README.md
```

---

## Design Choices & Tradeoffs

### Model: LLaMA 3.3 70B via Groq

**Why Groq?** Free tier, extremely fast (~500 tokens/sec), no credit card required.  
**Why LLaMA 3.3 70B?** Best open-weight model for instruction-following and structured JSON output. Consistent, high-quality evaluations.  
**Tradeoff:** Groq free tier has rate limits. For high-volume use, upgrade to paid or switch to OpenAI GPT-4o.

### Storage: JSON + CSV (no database)

**Why not SQLite?** JSON is human-readable, git-committable, and requires zero setup. For a CLI tool that runs dozens of sessions, not thousands, this is ideal.  
**Tradeoff:** No query support — you can't filter sessions by score. Easily upgradeable to SQLite by adding a few lines to `storage.py`.

### Scoring: Single LLM call per answer

**Why not batch?** Immediate feedback after each answer is better UX and matches how real interviewers work.  
**Tradeoff:** More API calls. Could be optimized with async concurrent scoring if speed is critical.

### Session resume: question-set deduplication

Resume works by building a `set()` of already-answered question strings and skipping them. This is O(1) lookup and works even if questions are reordered.  
**Tradeoff:** If the exact question text changes between versions, old sessions won't resume cleanly. A question ID would be more robust.

### What I'd improve with more time

- Add voice input (Whisper API) for spoken answers
- Web UI with FastAPI + HTMX for a browser-based experience
- Batch scoring to reduce API latency
- Export to PDF report with charts
- Multi-candidate comparison mode
- Configurable question types (behavioral, technical, system design)

---

## Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `groq` | ≥0.9.0 | Groq LLM API client |
| `python-dotenv` | ≥1.0.0 | Load API key from `.env` |
| `rich` | ≥13.7.0 | Terminal UI (panels, colors, tables) |

---

## Troubleshooting

**`GROQ_API_KEY not found`**  
→ Make sure you copied `.env.example` to `.env` and filled in your key.

**`ModuleNotFoundError: No module named 'groq'`**  
→ Run `pip install -r requirements.txt` inside your activated virtual environment.

**LLM returns non-JSON output**  
→ The `_extract_json()` helper in `interviewer.py` strips markdown fences and handles most edge cases. If it still fails, try setting `GROQ_API_KEY` to a different model by editing `MODEL` in `interviewer.py`.

**Rate limit errors**  
→ Groq free tier: ~30 requests/minute. Wait 60 seconds and retry, or upgrade your Groq plan.
