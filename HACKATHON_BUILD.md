# MathMate AI implementation audit — 2026-10-28

Positioning: **A Verification-First, Misconception-Aware Mathematics Learning Agent.**
Tagline: **Don't just solve it. Understand it.**

## Evidence and provenance

The earliest available Git checkpoint is `7b196ae` (2026-10-24), followed by generalized-maths checkpoints `4f74de3`, `412a09d`, and `657573f`. These establish checkpoint dates, not the date every feature was originally created. The hackathon start date and eligibility of pre-existing work have not been independently verified. Do not label all code as newly built for the hackathon. Many later classroom/OCR files are still uncommitted.

Existing baseline: authentication, SQLAlchemy persistence, migrations, deterministic maths, quiz/adaptation, OCR review, and frontend pages.
Later workspace work: universal question composer, broader maths, Mia classroom, local real-world visuals. Their exact creation chronology cannot be established from Git alone.
This stage adds: default-off Meta gate, persistent request/token reservations, authenticated-session limits, bounded session-scoped cache, explicit hosting configuration, strict structured-response validation, and offline contract tests.

## P0 status

| Area | Status | Evidence / remaining work |
|---|---|---|
| Restricted parser and SymPy solving | COMPLETE for implemented topics | Regression tests; not universal mathematics |
| First incorrect transformation | COMPLETE for supported equations | Existing analyze/confirm routes preserve student steps and corrected solution |
| Authentication and ownership | COMPLETE for local MVP | JWT/refresh rotation/CSRF/ownership tests; production deployment still unverified |
| Image/PDF ingestion and editable review | PARTIALLY IMPLEMENTED | File validation and fallback tests; handwriting quality and CPU latency remain limitations |
| Meta explanations/interpretation/transcription | PARTIALLY IMPLEMENTED | Transport and response schemas exist; real model inference NOT VERIFIED |
| Meta cost controls | PARTIALLY IMPLEMENTED | Offline-tested local limits; provider credit balance/charges not controlled by app |
| Mistake-to-Mastery state machine | NOT IMPLEMENTED | Current feedback, teaching, quizzes and recommendations are separate workflows |
| Adaptive practice | PARTIALLY IMPLEMENTED | Recent accuracy and hints change difficulty; no persistent misconception reassessment loop |
| Mia classroom | PARTIALLY IMPLEMENTED | Unified board, playback, interruption; approximate lip sync and procedural pointing |
| Avatar runtime | BROKEN in some observed interactions | Dev server recorded `undefined.resize` errors; reproduction and fix belong to P4 |
| Real-world visuals | PARTIALLY IMPLEMENTED | Five bounded local templates with numeric checks; not Meta-generated; browser shopping check performed |
| English/Tamil | PARTIALLY IMPLEMENTED | Local bilingual example text; Tamil voice and open-ended model quality NOT VERIFIED |
| UI consistency | PARTIALLY IMPLEMENTED | Topic example list remains long, obsolete Submit wording, wrapping controls, no topic search/level filters |
| PostgreSQL / deployment | NOT VERIFIED | Preserve SQLite; Docker work deferred by owner |
| Hackathon public repository | NOT VERIFIED | No publishing or push authorized/performed |

## P1 integration contract

Direct Meta: `https://api.meta.ai/v1/chat/completions`, Muse Spark 1.3 (`muse-spark-1.3`), backend `MODEL_API_KEY`.
Alternative hosting: Baseten `https://inference.baseten.co/v1/chat/completions`, `meta-models/muse-spark-open`, backend `BASETEN_API_KEY`. These are separate services and credit balances; a credit on one must not be assumed valid on the other.

Official sources checked on 2026-10-28:
- https://dev.meta.ai/docs/models
- https://dev.meta.ai/docs/protocols/chat-completions
- https://docs.baseten.co/inference/model-apis/overview
- https://docs.baseten.co/inference/model-apis/vision

Baseten Spark Open does not support structured-output/JSON mode according to its current feature documentation. The adapter requests plain JSON through instructions and validates it locally, rejecting incomplete or invalid output. It does not pretend this is constrained generation.

`META_ENABLED=false`, `AI_PROVIDER=mock`, and zero application budgets are safe defaults. Existing private `.env` keys were not printed or changed. No paid inference was performed. Live access, promotional credit, response quality and latency require an explicitly authorized test.

Request counts persist in the ignored `meta_usage.db`. A transaction reserves a request and byte-based input allowance plus output allowance before network access. Failed calls retain reservations; no automatic retries. This is conservative local accounting, not exact tokenization or a dollar billing cap. Actual usage is recorded when returned; prompts/images/responses are not written to this ledger. Do not delete it to reset a limit accidentally. All local workers must share its path; separate deployments do not share limits.

The in-memory cache is scoped to the authenticated refresh-token family, expires after ten minutes, and holds at most 128 entries. Single-process concurrent duplicate requests are coalesced. Separate workers can still duplicate requests, although shared ledger limits remain transactional. Access-token refresh retains the session family. Cache and usage accounting do not verify account credit balances.

## Stage order and deadline

- Oct 28: P0 audit and P1 guarded provider integration. Finish offline tests; authorize one bounded live request only after identifying the credit host.
- Oct 29: P2/P3 persisted mistake-to-mastery states, verified misconception evidence, targeted practice and reassessment.
- Oct 30: P4/P5 classroom runtime issues and focused UI consistency. Avoid avatar replacement or broad redesign.
- Oct 31: P6/P7 language and responsive checks, regression suite, documentation and demo rehearsal.
- Nov 1: code freeze and record only demonstrated capabilities.

P2 onward is not completed by this P0/P1 milestone. Do not present a local explanation as Meta inference or a rule-based quiz as a trained adaptive model.

## Verified checks for this checkpoint

- Backend: `python -m pytest -q` — 324 passed, 1 skipped, one dependency deprecation warning. Tests use synthetic data and isolated SQLite; no live inference.
- Frontend: 29 focused tests passed across real-world examples, classroom state, speech/gestures and question workflow.
- `npm run build` — passed, including TypeScript and static routes.
- Initial backend test failures came from test-origin configuration inheriting local port 3002; the test fixture now explicitly isolates port 3000. CSRF protection remains active.
- Browser evidence from the preceding visual stage: shopping scene appeared, narration automatically advanced to step 2, Pause retained progress, Next displayed the next equivalent calculation. Full responsive, Tamil-audio and avatar runtime verification remain pending.

Files changed in P0/P1: `backend/app/config.py`, `providers.py`, new `meta_usage.py`, `main.py`, `security.py`; backend provider/contract/input test files and fixture; both environment templates; README and the three root audit/architecture/demo documents. The earlier real-world frontend changes remain preserved.
