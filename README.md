# MathMate AI — Adaptive Visual Maths Tutor

**Don't just solve it. Understand it.**

MathMate AI is a **verification-first, misconception-aware maths learning application** built to help students understand *why* a solution works—not simply copy an answer. Students can check handwritten work, explore maths visually, and follow personalised practice missions with **Mia**, a 3D AI teaching companion. The experience supports **English and Tamil**.

Developed for the **Meta Global AI Developer Hackathon 2026**, with a documented pre-hackathon baseline and hackathon-stage additions.

> **The principle:** Meta Muse Spark can help interpret and explain. A bounded SymPy-based engine is responsible for mathematical verification and verdicts.

## Demo & documentation

- **Demo video:** Add the YouTube URL here once the final demo has been uploaded.
- **Screenshots:** Add screenshots or a short GIF of Check My Work, Mastery Mission, and Mia Learning Studio when ready.
- **Architecture diagrams:** [Project architecture](docs/project-architecture.svg) · [System design](docs/system-design.svg)
- **Technical details:** [ARCHITECTURE.md](ARCHITECTURE.md)
- **Hackathon work log:** [HACKATHON_BUILD.md](HACKATHON_BUILD.md)
- **Demo plan:** [DEMO_VIDEO_SCRIPT.md](DEMO_VIDEO_SCRIPT.md)

## Why MathMate AI?

A student can be told an answer is wrong without understanding *where the reasoning failed*. MathMate AI connects **verified step-by-step feedback** with guided explanation and practice based on past mistakes.

## Three core experiences

### 1. Check My Work — see where reasoning breaks

Students upload handwritten work or a PDF/DOCX worksheet, review the extracted transcription, and confirm the maths before grading. The verification engine checks successive lines and identifies the **first incorrect step**. Mia can then teach from the verified review; fraction misconceptions can lead to hands-on exploration in the Fraction Lab.

### 2. Autonomous Mastery Mission — practise the actual weakness

The mission reads verified mistake and quiz history, selects a target, shows a worked example, adapts drills and difficulty, and records its decisions in an **agent trace**. A role-reversal round can ask students to spot a deliberately incorrect line. The loop has explicit mastery and stop conditions rather than running indefinitely. Its routing and difficulty decisions are principally **rule-based**, using verified results rather than a separately trained learning model.

### 3. Mia Learning Studio — learn visually, in English or Tamil

Mia guides supported problems using a step-by-step KaTeX whiteboard, narration, follow-up explanations and real-world examples. The 3D teacher adds expression and gestures; mathematics remains subject to independent verification.

### Beyond the core

- **Math Treasure Journey:** A five-stage, gamified journey with gems, hints and a final stage informed by the learner's recorded weak topic.
- **Graph Playground:** Interactive function graphs and slope/intercept exploration.
- **Practice & Grow:** Server-graded quizzes, hints and adaptive difficulty.
- **My Progress:** Saved reviews, accuracy and topic-level learning history.


## Explore the app

| Area | Experience |
|---|---|
| Home | Topic explorer and learning entry points |
| Learning Studio | Whiteboard solutions, Mia narration and guided visuals |
| Graph Playground | Interactive graphs and slope/intercept exploration |
| Practice & Grow | Server-graded quizzes with hints |
| Mastery Mission | Mistake-driven adaptive practice and visible trace |
| Math Treasure Journey | Five-stage gamified learning route |
| Check My Work | Handwriting/document confirmation and step review |
| My Progress | Learning history, reviews and accuracy |
| Settings | Profile, English/Tamil narration and voice preferences |

## What makes it different

| A basic question-and-answer chatbot | MathMate AI |
|---|---|
| May produce a mathematical answer directly | Routes supported maths through a restricted symbolic verifier |
| Responds to individual prompts | Connects verified mistakes to targeted multi-step missions |
| Often lacks a verifiable grading trail | Shows the first incorrect line and a mission decision trace |
| Primarily text-based | Combines confirmed handwriting, fraction manipulation, whiteboard and 3D narration |

**Meta AI tooling:** Muse Spark contributes interpretation, transcription drafts, context-aware explanations and selected practice/wording drafts. Structured outputs and tool interfaces are bounded by validation. **SymPy, not Meta, decides mathematical correctness.** Provider labels, usage budgets and explicit local fallback make the model boundary inspectable. Not every autonomous action uses Meta: the mission and journey controllers are primarily deterministic, as documented in [ARCHITECTURE.md](ARCHITECTURE.md).

## How it works

```text
Student question / uploaded work
          |
          v
   Next.js frontend
          |
          v
      FastAPI API
       /    |    \
      /     |     \
SymPy maths  AI provider  Student data
verification Muse Spark  SQLite (local)
             or local   PostgreSQL (target)
             fallback
```

The **maths verification engine** checks supported expressions and steps. **Meta Muse Spark**, where enabled and available, contributes language-oriented capabilities such as explanation and transcription drafts. Students confirm extracted work before verification. When the model is unavailable or budget-capped, the UI identifies the local fallback rather than attributing its output to Meta.

For the detailed provider boundary, agent flows, security and budget handling, see [ARCHITECTURE.md](ARCHITECTURE.md).

## Tech stack

| Layer | Stack |
|---|---|
| Frontend | Next.js 16, React 19, TypeScript, KaTeX, JSXGraph, Recharts, React Three Fiber |
| Backend | Python, FastAPI, SQLAlchemy, Alembic, Pydantic, SymPy |
| AI | Meta Muse Spark via Baseten; labeled local/mock fallback |
| Data | SQLite for local development; PostgreSQL 17 configuration/target |
| 3D teacher | Three.js and React Three Fiber with browser speech synthesis |

## Getting started — Windows

**Requirements:** Node.js 22.13+ (Node 24 recommended), Python 3.13 or 3.14.

From the project root, run:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/setup-local.ps1
```

Start the backend and frontend **in separate PowerShell terminals**:

```powershell
# Terminal 1 — from project root
cd backend
.venv/Scripts/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

```powershell
# Terminal 2 — from project root
cd frontend
npm run dev
```

Open **http://localhost:3000** and register a local account. API documentation: **http://127.0.0.1:8000/docs**.

Never commit `backend/.env`, API keys, or `backend/meta_usage.db`. See [ARCHITECTURE.md](ARCHITECTURE.md) for configuration and budget controls.

## Adding your Meta API key

The repository ships **without any API key** (`backend/.env` is gitignored and never committed). Without one the app still runs fully — every Meta feature degrades to clearly labeled local behavior. To enable live Meta inference after cloning:

1. Get a key from **Baseten** (recommended — model `meta-models/muse-spark-open-1026`) or **direct Meta** (`muse-spark-1.3`).
2. Copy the template and edit it:

```powershell
copy backend\.env.example backend\.env
```

3. In `backend/.env`, set:

```env
AI_PROVIDER=meta
META_ENABLED=true
BASETEN_API_KEY=paste-your-key-here   # or MODEL_API_KEY=... for direct Meta
META_REQUEST_BUDGET=250               # deliberate cap; 0 fails closed
META_TOKEN_BUDGET=18000000
```

For direct Meta instead of Baseten, also set `META_HOST=meta` and `META_MODEL=muse-spark-1.3`.

4. Restart the backend. Verify at http://127.0.0.1:8000/docs → `GET /api/v1/tutor/status` (`configured: true`); the app header pill switches from "Local engine" to "Meta Muse Spark".

Usage is logged per call in ignored `backend/meta_usage.db`. Budgets estimate spend and do not guarantee zero charges.

## Verification & tests

```powershell
# Backend
cd backend
.venv/Scripts/python -m pytest -q
```

```powershell
# Frontend
cd frontend
npm run typecheck
node --experimental-strip-types --test scripts/test-*.mjs
npm run build
```

**Last reported in the supplied project documentation:** 432 backend tests passed, 1 skipped; 41 frontend checks, typecheck and build passed. These figures should be refreshed from the latest local CI/test run before publishing.

## Scope and limitations

This is a **locally verified prototype**, not a production deployment. Its documented maths scope emphasises linear equations, fractions and basic graphs. Extracted handwriting must be confirmed; the avatar's lip-sync is approximate. Long-term learning gains have not been established through a formal learner study. Deployment hardening and formal accessibility testing remain future work.

## Hackathon provenance

Authentication, persistence, deterministic maths, quizzes, OCR review and base pages existed before the hackathon baseline. Hackathon-stage work includes Meta provider agents and budgets, validated practice drafts, Mastery Mission, Treasure Journey and additional bilingual/visual learning features. For dates and boundaries, see [HACKATHON_BUILD.md](HACKATHON_BUILD.md).

## License and assets

Project license: MIT. The teacher avatar derives from Microsoft Rocketbox `Female_Adult_07`; see [ROCKETBOX-LICENSE.md](frontend/public/models/mia/ROCKETBOX-LICENSE.md). Other asset attributions are recorded in the project documentation.

© 2026 MathMate AI · Meta Global AI Developer Hackathon 2026
