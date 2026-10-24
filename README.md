# MathMate AI — Adaptive Visual Maths Tutor

A local full-stack hackathon MVP built with Next.js App Router, strict TypeScript, FastAPI, SQLAlchemy, and a bounded SymPy algebra engine. All project source is in this workspace. No real Meta inference or OCR is claimed without a configured and tested provider.

## Start locally on Windows

Requires Node.js 20.9+ (24 recommended) and Python 3.13 or 3.14.

```powershell
# From the mathmate-ai project root
powershell -ExecutionPolicy Bypass -File scripts/setup-local.ps1
```

The setup creates an ignored `backend/.env` with a random signing key, installs dependencies, runs Alembic, and seeds three lessons. It preserves existing configuration and records. SQLite is the local fallback so Docker is optional for development.

Run these in **two terminals**:

```powershell
cd backend
.venv/Scripts/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

```powershell
cd frontend
npm run dev
```

Open **http://localhost:3000**. Use exactly that hostname because the default CSRF origin is `http://localhost:3000`. Create your own account; there are no seeded passwords. API documentation: http://127.0.0.1:8000/docs.

If Python's `venv` cannot bootstrap pip, the setup also supports an existing virtual environment using the system pip's `--python` option. Manual equivalent:

```powershell
python -m venv --without-pip backend/.venv
python -m pip --python backend/.venv/Scripts/python.exe install -r backend/requirements.lock.txt
```

## PostgreSQL with Docker

Start Docker Desktop's Linux engine. Copy `.env.example` to `.env` and set a random `JWT_SECRET` and a strong URL-safe `POSTGRES_PASSWORD`. Do not use the example placeholders. Use alphanumeric database passwords or URL-encode reserved URL characters in the connection URL.

```powershell
docker compose up --build
```

The backend waits for PostgreSQL, applies the migration, seeds lessons, then serves the API. The frontend proxies `/api/v1` to the backend. PostgreSQL data persists in a named volume. Do not run `docker compose down -v` unless you intend to delete that database.

For a public deployment, configure HTTPS, `SECURE_COOKIES=true`, an exact `FRONTEND_ORIGIN`, unique secrets, and proxy rate/body limits. The in-memory authentication rate limiter is intended for a single-process MVP; use a shared limiter for multiple workers. There is no email verification, password reset, or account deletion flow in this milestone.

## Implemented

- Landing, registration, login, protected dashboard, topic explorer, studio, graphs, quizzes, work review, progress, and narration settings.
- Argon2 password hashing; 15-minute JWTs held in browser memory; HttpOnly SameSite refresh cookies; one-time refresh rotation; reuse detection and logout family invalidation; origin plus custom-header CSRF checks.
- User ownership on private API resources; private data never included in anonymous server-rendered app HTML.
- Linear equations with integer/decimal/fraction coefficients and implicit multiplication. Safe recursive-descent parsing without `eval`, `sympify(student_text)`, or arbitrary function calls.
- Unique/no/infinite solutions; division-by-zero rejection; bounded syntax; solution-set equivalence and first incorrect line detection.
- KaTeX whiteboard with step navigation, narration transcript, and lesson completion.
- JSXGraph slope/intercept playground; numerical graph API; Recharts learning history.
- Server-owned quiz questions and hints, immutable submitted attempts, deterministic scoring, topic difficulty, recent accuracy, and explained recommendations.
- PNG/JPEG/WebP validation, bounded image dimensions and size, editable transcription with explicit confirmation, saved feedback, and manual fallback.
- AIProvider interface, labeled MockAIProvider, documented MetaAIProvider using HTTPX, timeout handling and fallback. See `docs/meta-integration.md`.
- Browser voice selection, play/replay, pause/resume, stop, mute, and step-change cancellation. Mia uses a licensed Microsoft Rocketbox-derived rigged 3D human model, rendered with React Three Fiber. Blinking, head motion, smiles, breathing and approximate speech-driven jaw movement accompany lesson and quiz states. See docs/teacher-3d.md for asset licensing and voice limitations.
- All 16 requested data tables, frozen initial Alembic migration, non-destructive timestamp migration, repeatable seed, Docker manifests, and CI workflow.
- Profile-name editing, saved lesson-session starts, typed response contracts, categorized mistakes, and an explicit provider-configuration status endpoint.

The workspace uses tabs within `/app` for its authenticated screens. API authorization is enforced on every protected endpoint; client navigation is not the security boundary. Access tokens are never stored in localStorage.

## Tests and builds

```powershell
cd backend
.venv/Scripts/python -m pytest -q
```

```powershell
cd frontend
npm run build
npm run typecheck
```

Tests exercise algebra attacks and edge cases, valid/invalid transformations, authentication rotation/replay/logout, CSRF, ownership, scoring, adaptive rules, uploads, confirmation, saved progress, and an API-level learning journey. Test databases are isolated in memory. See `docs/verification.md` for actual results and environment limitations.

## Demo route

1. Register → dashboard → The art of balance.
2. Explore `2x + 3 = 11`; advance through the steps; play narration; complete the lesson.
3. Move slope and intercept in Graph playground.
4. Complete practice questions; use a hint; inspect My progress.
5. Check my work → enter `2x+3=11`, `2x=8`, `x=5` on separate lines → confirm → see line 3 flagged and the corrected result.
6. Optionally upload a real photo. Without Meta configured, manually transcribe it; the UI does not claim OCR occurred.

## Scope and next milestone

This is a verified local MVP, not a production deployment. Remaining external gates are a real Meta text/vision integration test with credentials and PostgreSQL/Docker runtime verification. Higher-fidelity facial performance, phoneme-timed lip synchronization, password recovery/email verification, distributed rate limiting, and a formal accessibility audit remain future work. The current teacher is real rigged 3D geometry with procedural motion, not a video or flat illustration. The validator compares equation solution sets and gives a specific explanation when only one side changes; it does not infer every possible student operation. Final substitution checks are intentionally separate from equivalent-equation transformations. Raw handwritten photos are not retained or retrievable.

AI chat currently has one request's verified equation context; messages are saved but multi-turn conversational history retrieval is not yet exposed. Progress uses recent accuracy, not a claim of inferred long-term mastery. No third-party service has been deployed by this task.

## Production build and local preview

```powershell
cd frontend
npm run build
npm run start
```

The build uses webpack because Turbopack failed launching its CSS worker on this Windows machine. The start helper serves Next's standalone output and copies its static assets. Start the backend separately as shown above. Use `http://localhost:3000` for browser access even when the server prints `127.0.0.1`.

Backend dependencies are frozen in `backend/requirements.lock.txt`; the direct dependency ranges remain in `backend/requirements.txt`. The frontend uses `package-lock.json`. No lint script was configured; production compilation and strict TypeScript checking are the frontend checks.

## Optional PostgreSQL verification

The Docker engine was unavailable during local verification. An offline PostgreSQL migration script is included in `docs/postgres-schema.sql`; it is a static check, not proof of a live database connection. The CI PostgreSQL job runs migrations and a persistence test against PostgreSQL 17. CI has been configured but has not been run remotely.

To run that test locally with a PostgreSQL account permitted to create schemas:

```powershell
cd backend
$env:TEST_POSTGRES_URL='postgresql+psycopg://user:password@localhost/test_database'
.venv/Scripts/python -m pytest tests/test_postgres.py -q
```

It creates and removes only a uniquely named temporary schema. It never drops existing application schemas. Without `TEST_POSTGRES_URL`, this test reports a skip.

Your existing SQLite file was backed up under ignored `backend/backups/` before migration `0002`. Existing rows were preserved. Local browser QA created a test account (`demo.qa.20261023@example.com`) and saved lesson/quiz/review records; those records were not deleted.

## Repository

`frontend/src/app` — routes and styling; `frontend/src/components` — learning UI; `backend/app` — API, security, maths, providers, models; `backend/tests` — test suite; `backend/alembic` — migrations; `scripts` — local setup; `docs` — integration and verification notes.
