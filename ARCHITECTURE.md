# MathMate AI — Architecture

Companion diagrams: [Project Architecture](docs/project-architecture.svg) · [System Design](docs/system-design.svg) · [Agent Architecture](docs/agent-architecture.svg)  
Hackathon development history: [HACKATHON_BUILD.md](HACKATHON_BUILD.md) · [Project README](README.md)

> **Documentation status:** This document describes the implementation reported in the supplied project documentation. Exact behavior, file paths, flags, and test counts should be checked against the current repository before publication.

## 1. System overview

```text
Browser
   │
   │ /api/v1 (same-origin proxy)
   ▼
Next.js frontend
   │
   ▼
FastAPI backend
   ├── Deterministic maths engines
   │      SymPy · restricted parser · isolated workers
   │
   ├── AI provider boundary
   │      Meta Muse Spark (language/drafts only)
   │      MockAIProvider (labeled fallback)
   │
   └── Persistence
          SQLite (local development)
          PostgreSQL 17 (production target)
```

Three principles govern the design:

1. **Verification boundary.** Solving, grading, mathematical step checks and verdicts are controlled by deterministic code, not by model-generated prose.
2. **Confirm before trust.** Model-generated transcription and interpretation drafts are reviewed, confirmed, or revalidated before their mathematical consequences are trusted.
3. **Budgeted autonomy.** Model requests pass through configured provider gates and a usage ledger; exhausted budgets lead to an explicitly labeled local fallback.

## 2. Frontend — Next.js 16, React 19, TypeScript

The application has public landing and authentication pages and an authenticated `/app` workspace, with sidebar navigation, a provider-status indicator and a `MiaPanel` companion available across supported views.

| Route/view key | User-facing view | Primary component and purpose |
|---|---|---|
| `topics` | Home | `explore-topics.tsx` — greeting, topics, recommendations and lesson entry points |
| `learn` | Learning Studio | `question-input.tsx`, `question-teaching.tsx` — supported problems, verified explanations, construction guides, real-world examples and Fraction Lab |
| `whiteboard` | Mia's Whiteboard (from Home) | `teaching-lesson.tsx` — three guided lessons |
| `graph` | Graph Playground | `graph.tsx` — JSXGraph slope/intercept playground and function graphs |
| `quiz` | Practice & Grow | `quiz.tsx` — quizzes, hints and adaptive difficulty |
| `mission` | Mastery Mission | `mission.tsx` — diagnosis, practice, verdict and trace |
| `journey` | Math Treasure Journey | `journey.tsx` — five-stage roadmap, gems and lifelines |
| `handwriting` | Check My Work | `handwriting.tsx` — uploads, transcription confirmation, line-by-line review, teaching and practice |
| `progress` | My Progress | `progress.tsx` — history, accuracy, charts and recommendations |
| `settings` | Settings | `settings.tsx`, `profile-editor.tsx` — language, voice and profile settings |

`whiteboard` is an entry point within the workspace; it is not counted as one of the nine primary navigation tabs.

**Shared client-side systems**

- `teacher.tsx` and `mia-whiteboard.tsx`: KaTeX board rendering, step state and narration synchronization.
- `teacher-avatar.tsx`: React Three Fiber and the rigged `teacher.glb` avatar.
- `lib/mia-voice.ts` and `lib/teaching-language.ts`: voice selection, English/Tamil narration and visual triggers; Clara is documented as the default English voice.
- `lib/api.ts` and React Query: API communication and data fetching; access JWTs are documented as held in memory.
- Production build is documented as webpack/standalone, owing to Turbopack CSS-worker issues on the development Windows machine.

## 3. Backend — FastAPI `/api/v1`

`backend/app/main.py` connects approximately 50 reported API endpoints, with functionality separated across modules:

| Module(s) | Responsibility |
|---|---|
| `agents/` | `mia_orchestrator`, `orchestrator`, `teaching`, `practice`, `vision`, `maths`, `tools` — sessions, turns, teaching, validated practice and model-facing agent tools |
| `math_parser`, `math_runtime`, `maths` | Restricted parsing (no `eval`, no `sympify(student_text)`), isolated-worker SymPy execution, mathematical equivalence and first-incorrect-line checks |
| `calculus`, `advanced_maths`, `linear_algebra`, `topic_maths` | Extended topic-specific maths and worked steps |
| `construction`, `fraction_work` | Bilingual ruler-and-compass guidance and fraction misconception analysis for the lab |
| `question_input` | Free-form question routing and interpretation review |
| `work_review` | Line-by-line work review with error codes such as `fraction_addition` and `inverse_operation` |
| `missions`, `journey` | Bounded learning loops exposed by `/mission/*` and `/journey/*` |
| `providers` | `AIProvider`, `MockAIProvider`, `MetaAIProvider` with HTTPX, timeouts and structured outputs |
| `document_text`, `docx_text`, `local_vision` | PDF/DOCX extraction and local OCR/vision paths |
| `security`, `models`, `db`, `config`, `schemas`, `seed` | Authentication, ORM models, sessions, configuration, request/response contracts and lesson seeds |

## 4. Verification boundary — what Meta may and may not do

| Meta surface | Method | Enforced boundary described in documentation |
|---|---|---|
| Chat explanations | `explain` | Receives verified context and returns explanatory text; does not issue grading verdicts |
| Handwriting transcription | `transcribe` | Produces an editable draft that the student confirms; original image is not retained |
| Question interpretation | `interpret` | Parses intent/routing; deterministic maths engines solve supported problems |
| Teaching reviewed work (English/Tamil) | `teach_work` | Explains already-verified work feedback |
| Real-world narration | Provider path under `/tutor/real-world` | Reuses verified problem quantities; provider label is shown |
| Practice drafts | `draft_practice` | Proposed values pass difficulty checks; equation **and** answer are recomputed and checked by deterministic tools; failures fall back to deterministic drills |
| Flavor text | `flavor` | Short encouraging text for quizzes, progress and mission briefs; can be empty when Meta is disabled |

Provider calls are gated through `meta_active()` using the configuration reported below: `AI_PROVIDER=meta`, `META_ENABLED`, an optional `META_ENABLED_UNTIL` expiry, and remaining request/token budget. The UI is documented as showing live provider status through `GET /tutor/status` (under the API prefix), distinguishing **Meta Muse Spark** from **Local engine**.

The documented agent framework also supports structured-output and tool-call paths; their *actual live model invocation* should be demonstrated from real request logs or traces rather than inferred from the existence of code paths.

## 5. Bounded autonomous learning loops

**Important distinction:** Mastery Mission and Treasure Journey are described as adapting through **rules over verified results**, not through a separately trained learning model. Their recorded decisions are presented in a visible trace.

### 5.1 Mastery Mission — `missions.py`

```text
Saved work reviews + quiz history
               │
               ▼
      diagnose() weakest error
               │
               ▼
      Verified worked example
               │
               ▼
      Targeted adaptive drills ──► Grade with SymPy
               │                       │
               └◄──── adjust difficulty / re-plan
                                       │
                                       ▼
                         Mastery or bounded stop
                                       │
                                       ▼
                         Verdict + trace + history
```

According to the supplied architecture description:

- `diagnose()` considers persisted reviews and quiz performance, prioritizing recurring verified errors and excluding just-mastered targets.
- Worked examples precede targeted drills; the mission serves up to **10** fresh drills and avoids recently repeated equations.
- Two correct answers in a row raise difficulty, up to level **3**.
- Low accuracy can trigger a downward re-plan, documented as at most **2** re-plans.
- A role-reversal round may challenge the student to spot a deliberately incorrect step.
- **Three consecutive correct answers** meet the mastery exit criterion; **three wrong answers total** trigger a bounded stop with verified answers.
- The final verdict reports before/after accuracy and a decision trace.

### 5.2 Treasure Journey — `journey.py`

Five stages are documented: **equations → fractions → graphs → deeper fractions → a boss stage based on the diagnosed weakest topic**.

- Three earned gems conquer an island, with difficulty rising across gems.
- Incorrect answers retry the same question, up to three attempts before teaching feedback.
- Hint, nudge and reveal lifelines support recovery; revealed answers do not earn gems.
- A non-conquered stage can be marked **needs practice** after eight tries, allowing the journey to continue.
- Per-stage status, learning trace and before/after accuracy are reported.

## 6. Data and persistence

- **ORM:** SQLAlchemy 2.1.6, with authorization/ownership constraints on private student resources.
- **Migrations:** Alembic, including a frozen initial baseline and documented non-destructive timestamp migration/seed behavior.
- **Local database:** SQLite.
- **Production target:** PostgreSQL 17, with Docker and CI artifacts; the supplied documentation does not claim a verified public deployment.
- **Provider accounting:** An ignored local `meta_usage.db` database, separate from student data, with a `calls` table for hashed session IDs, reserved/actual tokens, estimated USD and timestamps.

Do not commit `backend/.env`, API keys, or provider-usage records containing potentially sensitive metadata.

## 7. Authentication and security

The documented controls include:

- Argon2 password hashing.
- 15-minute JWT access tokens stored in browser memory rather than localStorage.
- HttpOnly SameSite refresh cookies with one-time rotation, reuse detection and refresh-family invalidation.
- Origin and custom-header CSRF checks.
- Server-side authorization of protected resources (navigation visibility is not the security boundary).
- Bounded PNG/JPEG/WebP uploads, including file-size and image-dimension limits.
- No retention of raw handwritten photos in the described review flow.
- Validated refresh-family identity scoped in backend request state for provider accounting; clients do not select that identity.

These are reported implementation controls, not a certification or proof of complete child-safety/security compliance.

## 8. Configuration

| Variable | Purpose |
|---|---|
| `AI_PROVIDER` | Select `meta` or `mock` |
| `META_ENABLED` | Enable/disable Meta requests |
| `META_ENABLED_UNTIL` | Optional provider-enablement expiry (`0` = no expiry, per supplied documentation) |
| `META_REQUEST_BUDGET` | Request count cap |
| `META_TOKEN_BUDGET` | Token budget cap |
| `MODEL_API_KEY`, `BASETEN_API_KEY` | Credential holder for direct Meta or Baseten access (model name reported as `meta-models/muse-spark-open`) |
| `FRONTEND_ORIGIN` | Exact allowed frontend origin |
| `SECURE_COOKIES` | HTTPS cookie security setting |
| `JWT_SECRET` | Access-token signing secret |

**Billing caveat:** Local budget accounting estimates usage but does not guarantee a zero external charge. Never publish credentials or `.env` files.

## 9. Verification and reproducibility

The supplied documentation reports the following **previously run** checks; they have not been rerun as part of preparing this file:

| Check | Reported outcome |
|---|---|
| Backend `pytest` | **432 passed, 1 skipped** |
| Frontend TypeScript | `tsc --noEmit` passed |
| Frontend Node tests | **41** checks passed |
| Frontend production build | `npm run build` passed |
| PostgreSQL integration checks | Run in CI; skipped locally without `TEST_POSTGRES_URL` |

Coverage is described as including algebra attacks, transformations, authentication refresh/replay/logout, CSRF, ownership, scoring, adaptive rules, upload confirmation, progress persistence and an API-level learning journey. See [docs/verification.md](docs/verification.md).

## 10. Deployment shape

### Local development

```text
http://localhost:3000         Next.js dev server
       │
       └── /api/v1 ──► http://127.0.0.1:8000  FastAPI/Uvicorn
```

From the repository root, start the backend and frontend in separate Windows PowerShell terminals:

**Backend**

```powershell
cd backend
.venv/Scripts/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

**Frontend**

```powershell
cd frontend
npm run dev
```

### Production target

The described production path includes `npm run build` followed by `npm run start` (standalone Next.js output) and a FastAPI backend behind HTTPS. Before publishing, configure:

- Exact `FRONTEND_ORIGIN`.
- `SECURE_COOKIES=true` and unique deployment secrets.
- Reverse-proxy request-body and rate limits.
- A shared authentication rate limiter when using multiple workers (the documented in-memory limiter is single-process).
- Appropriate service and database monitoring.

Docker manifests and a GitHub Actions pipeline with linting, tests, build and PostgreSQL checks are described as included. Production readiness still requires deployment-time validation.

---

**MathMate AI** · Don't just solve it. Understand it.  
For the high-level feature showcase, see [README.md](README.md). For historical attribution and the hackathon work split, see [HACKATHON_BUILD.md](HACKATHON_BUILD.md).
