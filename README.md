# MathMate AI — Adaptive Visual Maths Tutor

**Don't just solve it. Understand it.**

**One Meta AI model. Seven specialised capabilities. Coordinated agent workflows. Four connected learning experiences.**

MathMate AI is a **verification-first, misconception-aware mathematics learning application** that helps students understand *why* a solution works—not simply copy an answer. Students can check handwritten work, explore maths visually, follow personalised practice missions, and learn with **Mia**, an interactive 3D AI teaching companion. The experience supports **English and Tamil**.

Developed for the **Meta Global AI Developer Hackathon 2026 (Indie track)**, with a documented pre-hackathon baseline and hackathon-stage additions.

> **Core principle:** Meta Muse Spark can interpret, draft, and explain. A bounded **SymPy-based engine** decides mathematical correctness for supported problem types.

## 🎬 Demo & documentation

- **Demo video:** [Watch MathMate AI on YouTube](https://youtu.be/IMvKsh4gJ7w)
- **Architecture diagrams:** [Project architecture](docs/project-architecture.svg) · [System design](docs/system-design.svg)
- **Technical architecture:** [ARCHITECTURE.md](ARCHITECTURE.md)
- **Hackathon work log:** [HACKATHON_BUILD.md](HACKATHON_BUILD.md)
- **Demo plan:** [DEMO_VIDEO_SCRIPT.md](DEMO_VIDEO_SCRIPT.md)

## Why MathMate AI?

Students are often told an answer is wrong without understanding *where their reasoning failed*. Repeating this experience can undermine confidence, especially for students who hesitate to ask questions or prefer learning in their own language.

MathMate AI connects **verified, step-by-step feedback** with guided explanation, visual exploration, and practice informed by previous mistakes. The aim is to turn *“I got it wrong”* into *“Now I understand.”*

## Four core learning experiences

### 1. Check My Work — see where reasoning breaks

Students upload handwritten work or a **PDF/DOCX worksheet**, review the extracted transcription, and confirm the maths before grading. The verification engine checks successive lines and identifies the **first detected incorrect step** within its supported scope.

Mia can then teach from the verified review. Fraction misconceptions can lead to hands-on exploration in the **Fraction Lab**.

### 2. Autonomous Mastery Mission — practise the actual weakness

The mission reads verified mistake and quiz history, selects a learning target, shows a worked example, adapts drills and difficulty, and records its decisions in an **agent trace**.

A role-reversal round may ask students to spot a deliberately incorrect line. The loop includes explicit mastery and stopping conditions rather than running indefinitely.

**Important:** Mission routing and difficulty decisions are principally **rule-based**, using verified results—not a separately trained adaptive learning model.

### 3. Mia Learning Studio — learn visually, in English or Tamil

Mia guides supported maths problems with a step-by-step **KaTeX whiteboard**, narration, follow-up explanations, and everyday examples. The 3D teacher adds expressions and gestures, while mathematics remains subject to independent verification.

### 4. Math Treasure Journey — turn practice into an adventure

Math Treasure Journey is an interactive **five-stage** gamified experience. Students navigate a 3D learning environment, solve verified maths challenges, receive hints, collect gems, and progress through mathematical problem-solving.

Challenges can draw on recorded weak topics, including a targeted final stage. Meta-assisted narrative content can support the experience; **deterministic checking**, not the language model, determines correctness for supported challenges. Journey progression itself is primarily deterministic.

### Beyond the core

- **Fraction Lab:** Hands-on fraction representations and exploration.
- **Graph Playground:** Interactive graphs and slope/intercept exploration.
- **Practice & Grow:** Server-graded quizzes, hints, and adaptive difficulty.
- **My Progress:** Saved reviews, accuracy, and topic-level learning history.

## 🤖 Meta AI and multi-agent architecture

### One Meta model, seven specialised capabilities

MathMate AI integrates **Meta Muse Spark Open through Baseten** as a shared AI inference capability.

**Instead of deploying seven separate AI models, we reuse one Meta model across seven specialised capabilities:**

1. **Handwriting Transcription:** Drafts interpretations of mathematical working from uploaded images.
2. **Question Interpretation:** Helps understand students' mathematical questions and requests.
3. **Bilingual Teaching:** Produces explanation drafts in Tamil and English.
4. **Real-World Examples:** Connects mathematical concepts to everyday situations.
5. **Practice Generation:** Drafts targeted exercises, subject to validation.
6. **Conversational Tutoring:** Supports Mia's follow-up explanations and clarification responses.
7. **Game Narratives:** Provides contextual educational wording for Math Treasure Journey.

These are **seven model-supported capabilities**, not a claim of seven separately deployed AI models or seven independent autonomous agents. Live Meta-backed functionality depends on provider configuration, available credits/budget, and the supported workflow; the application distinguishes local fallback from actual Meta inference.

### How the coordinated workflows operate

The application coordinates specialised responsibilities for:

- **Handwriting interpretation:** Extracting draft mathematical steps for students to confirm.
- **Mathematical/question understanding:** Interpreting the learning request and supported problem type.
- **Teaching and explanation:** Using verified results to support contextual, bilingual feedback.
- **Practice generation:** Preparing relevant exercises and applying validation.
- **Adaptive mission control:** Selecting learning targets and difficulty from verified learning history, with explicit rules and traceable decisions.

These describe **workflow responsibilities**, not an exhaustive source-verified list of class or module names. See [ARCHITECTURE.md](ARCHITECTURE.md) for the implementation-level agent/provider boundaries.

**Check My Work flow**

```text
Student upload
    ↓
Handwriting interpretation
    ↓
Student confirms extracted maths
    ↓
SymPy step-by-step verification
    ↓
First detected incorrect step + verified review
    ↓
Mia's guided explanation
    ↓
Saved learning context → targeted practice
```

**Autonomous Mastery Mission flow**

```text
Verified mistake and quiz history
    ↓
Rule-based weakness / target selection
    ↓
Worked example and targeted drills
    ↓
Verified answers and feedback
    ↓
Difficulty adjustment + agent trace
    ↓
Mastery or explicit stopping condition
```

### Why separate AI assistance from mathematical verification?

The model supports language-oriented interpretation, explanation, and selected content drafts. **SymPy, not Meta, determines mathematical correctness** for the application's supported operations.

Structured outputs and tools are bounded by validation. Provider labels, request/token budgets, and explicit local fallback make the model boundary inspectable. Not every autonomous action invokes Meta; **mission and journey controllers are primarily deterministic**.

## Explore the app

| Area | Experience |
|---|---|
| Home | Topic explorer and learning entry points |
| Learning Studio | Whiteboard solutions, Mia narration, and guided visuals |
| Fraction Lab | Hands-on fraction exploration |
| Graph Playground | Interactive graphs and slope/intercept exploration |
| Practice & Grow | Server-graded quizzes with hints |
| Mastery Mission | Mistake-driven adaptive practice and visible agent trace |
| Math Treasure Journey | Five-stage gamified learning route |
| Check My Work | Handwriting/document confirmation and step review |
| My Progress | Learning history, reviews, and accuracy |
| Settings | Profile, English/Tamil narration, and voice preferences |

## What makes it different

| Basic question-and-answer chatbot | MathMate AI |
|---|---|
| May produce a final answer directly | Routes supported maths through a restricted symbolic verifier |
| Responds to isolated prompts | Connects verified mistakes to targeted multi-step missions |
| May lack a verifiable grading trail | Shows the first detected incorrect step and mission decision trace |
| Primarily text-based | Combines confirmed handwriting, fraction manipulation, whiteboard, and 3D narration |

## How it works

```text
Student question / uploaded work
               |
               v
         Next.js frontend
               |
               v
           FastAPI API
          /     |      \
         v      v       v
  SymPy maths  AI provider  Student data
  verification Muse Spark   SQLite (local)
               or labelled  PostgreSQL (target)
               local fallback
```

The **maths verification engine** checks supported expressions and steps. **Meta Muse Spark**, where enabled and available, contributes explanation and transcription drafts and other selected language-oriented capabilities. Students confirm extracted work before verification. If Meta inference is unavailable or budget-capped, the UI identifies the local fallback instead of attributing that output to Meta.

For provider boundaries, agent flows, security, and budgets, see [ARCHITECTURE.md](ARCHITECTURE.md).

## Tech stack

| Layer | Stack |
|---|---|
| Frontend | Next.js 16, React 19, TypeScript, KaTeX, JSXGraph, Recharts, React Three Fiber |
| Backend | Python, FastAPI, SQLAlchemy, Alembic, Pydantic, SymPy |
| AI | Meta Muse Spark Open via Baseten; labelled local/mock fallback |
| Data | SQLite for local development; PostgreSQL 17 configuration/target |
| 3D teacher | Three.js and React Three Fiber with browser speech synthesis |

## Who can benefit?

- **School students:** Understand mistakes through verified feedback and visual, targeted practice.
- **Students hesitant to ask questions:** Explore concepts with a supportive, conversational companion.
- **Tamil- and English-speaking learners:** Receive explanations in a preferred supported language.
- **Students with limited access to individual tutoring:** Use an additional independent learning resource.
- **Parents:** Support children's maths practice.
- **Teachers and tuition centres (future):** Potentially use teacher-reviewed activities and learning insights to complement classroom teaching.

## Getting started — Windows

**Requirements:** Node.js 22.13+ (Node 24 recommended), Python 3.13 or 3.14.

From the project root:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/setup-local.ps1
```

Start the backend and frontend **in separate PowerShell terminals**:

**Terminal 1 — backend**

```powershell
cd backend
.venv/Scripts/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

**Terminal 2 — frontend**

```powershell
cd frontend
npm run dev
```

Open **http://localhost:3000** and register a local account. API documentation is at **http://127.0.0.1:8000/docs**.

Never commit `backend/.env`, API keys, or `backend/meta_usage.db`. See [ARCHITECTURE.md](ARCHITECTURE.md) for configuration and budget controls.

## Adding your Meta API key

The repository ships **without an API key** (`backend/.env` is gitignored). Without a configured key, the application can run in clearly labelled local fallback mode.

To enable live Meta inference after cloning:

1. Obtain a key from **Baseten** (documented model: `meta-models/muse-spark-open-1026`) or **direct Meta** (documented model: `muse-spark-1.3`).
2. Copy the template:

   ```powershell
   copy backend\.env.example backend\.env
   ```

3. Configure `backend/.env`:

   ```env
   AI_PROVIDER=meta
   META_ENABLED=true
   BASETEN_API_KEY=paste-your-key-here
   META_REQUEST_BUDGET=250
   META_TOKEN_BUDGET=18000000
   ```

   For direct Meta instead of Baseten, the existing project documentation specifies `MODEL_API_KEY`, `META_HOST=meta`, and `META_MODEL=muse-spark-1.3`.

4. Restart the backend. Check **http://127.0.0.1:8000/docs** → `GET /api/v1/tutor/status` for provider configuration/status.

Usage is logged per call in ignored `backend/meta_usage.db`. Budget controls estimate and limit configured usage, but **do not guarantee zero charges**.

## Verification & tests

**Backend**

```powershell
cd backend
.venv/Scripts/python -m pytest -q
```

**Frontend**

```powershell
cd frontend
npm run typecheck
node --experimental-strip-types --test scripts/test-*.mjs
npm run build
```

**Fresh-clone backend test result (November 2026):** **432 passed, 1 skipped, 1 warning**.

The previously documented frontend result was **41 frontend checks passed**, with typecheck and build passing at that time. Re-run the frontend checks from the current fresh clone before claiming a newly verified result.

## Scope and limitations

MathMate AI is a **locally verified prototype**, not a production deployment. Its documented maths scope emphasises **linear equations, fractions, and basic graphs**. Handwriting extraction requires student confirmation; the avatar's lip-sync is approximate. Long-term learning gains have **not** been established through a formal learner study. Deployment hardening and formal accessibility testing are future work.

Some teaching and narrative capabilities use Meta only when the provider is enabled and available. The deterministic mission and journey controllers should not be described as fully autonomous, continuously model-driven agents.

## Future goals

- Broaden the supported maths curriculum and visual learning activities.
- Expand teacher-reviewed exercises and learning resources.
- Add richer student progress dashboards and learning analytics.
- Support tuition teachers with relevant insights and classroom-friendly workflows.
- Improve deployment readiness, accessibility, and affordable access.

The long-term vision is to make **personalised, bilingual mathematics learning** more accessible while complementing human teachers.

## Hackathon provenance

Authentication, persistence, deterministic maths, quizzes, OCR review, and base pages existed before the hackathon baseline. Hackathon-stage work includes Meta provider agents and budgets, validated practice drafts, Mastery Mission, Treasure Journey, and additional bilingual/visual learning features.

For dates and boundaries, see [HACKATHON_BUILD.md](HACKATHON_BUILD.md).

## License and assets

**Project license:** MIT.

The Mia teacher avatar derives from Microsoft Rocketbox `Female_Adult_07`. See [ROCKETBOX-LICENSE.md](frontend/public/models/mia/ROCKETBOX-LICENSE.md). Other asset attributions are recorded in the project documentation.

---

© 2026 MathMate AI · Meta Global AI Developer Hackathon 2026

**Don't just solve it. Understand it.**
