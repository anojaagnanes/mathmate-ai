# Generalized maths — Phase 1

Implemented 2026-10-24. Pre-change local Git checkpoint: `7b196ae`. No database reset, new dependency, deployment or paid service.

## Supported

- Real variables: x, y, z, n, a, b, c, t, u, v, theta, alpha, beta (up to three per expression side).
- Exact integers, decimals, fractions, bounded scientific notation; + - * /, parentheses, implicit multiplication.
- Integer powers (-6 through 6 for numeric bases; positive powers through 6 for variable bases), ^ and **, Unicode squared/cubed, numeric sqrt() and √.
- Polynomial expression expansion/collection up to total degree 6; equations up to degree 2.
- Single-variable linear and quadratic real roots, repeated roots, contradictions, identities; substitution checks for every root.
- Multivariable input prompts for a target. Linear isolation with a nonzero numeric coefficient returns a parametric answer, not unique numerical values.
- Typed questions, confirmed handwriting equations, quizzes and tutor use the same parser and solver.
- Single-variable linear/quadratic student-step checks preserve complete solution sets, including both quadratic roots.

## Security and boundaries

A strict tokenizer and recursive-descent grammar build a syntax tree before explicitly constructing SymPy objects. No eval, exec, parse_expr or unrestricted sympify on student input. Rejects arbitrary names, attribute access, lists and Python calls.

Limits: 200 characters, 80 tokens per expression side, 100 syntax nodes, depth 15, three symbols per side, 12-digit numeric literals, scientific exponent magnitude 12, 512-bit intermediate rationals, 150 symbolic operations, polynomial degree 6 and 100 terms. API calculations run in spawned child processes with an eight-second deadline and four concurrent slots per server process; timed-out workers are terminated. Worker startup is included in the deadline. This adds some latency, especially on Windows. These are application limits, not an OS memory sandbox or deployment-wide rate limiter.

Not yet supported: variable denominators (including 1/x=0), variable square roots, symbolic zero/negative powers, general symbolic coefficients requiring case splits, equations of degree >2, systems, inequalities, trigonometry/logarithms/constants pi/E, calculus, matrices, statistics, sequences and complex roots. Unsupported requests return HTTP 422 with an explanation. x²=-1 is correctly reported as no REAL solutions, not no complex solutions.

The existing straight-line graph and quiz curriculum remain intentionally linear. No OCR recognition/PDF extraction was added in this maths phase. Meta remains unverified development mode unless separately configured. Mia's current avatar and voice system are preserved; its responses use the expanded deterministic result and selected variable.

## Changed files

- backend/app/math_parser.py — new grammar and resource bounds.
- backend/app/math_runtime.py — new killable worker boundary.
- backend/app/maths.py — generalized arithmetic/algebra/linear/quadratic handling and step analysis.
- backend/app/main.py — shared runtime, target variable, any-symbol quiz rejection, nonblocking tutor calculation.
- backend/app/schemas.py — result kinds, roots, variable/topic/domain, optional step LaTeX.
- backend/app/providers.py — topic-aware fallback and expanded deterministic result instructions.
- backend/tests/test_general_math.py — new functional, domain, security, runtime and API tests.
- backend/tests/test_maths.py — moved newly supported powers/products from rejection cases to positive coverage; retained remaining security and regression cases.
- frontend/src/app/app/page.tsx — question controls, examples, variable selection, topic/results/LaTeX.
- frontend/src/lib/types.ts — expanded result contract.
- frontend/src/components/teacher.tsx — target variable forwarded to tutor.
- frontend/src/components/handwriting.tsx — verified steps rendered using supplied LaTeX.
- frontend/next-env.d.ts — Next-generated production type paths.
- docs/math-phase1.md — this report.

## Verification

- Full backend suite: 105 passed, 1 skipped, 0 failed. Optional PostgreSQL test skipped without a configured test database; existing Starlette/httpx deprecation warning remains.
- Frontend production build: passed.
- TypeScript check: passed.
- Existing teacher-performance script: 6 passed; existing Node module-type warning remains.
- No lint command is configured.
- Browser: generalized y equation, quadratic two-root result, and exact irrational arithmetic (sqrt(10)) confirmed using the production frontend and live backend. Mia rendered and its transcript followed the selected solution step. Screenshot: screenshots/math-phase1.jpg. Full audio playback was not retested in this phase.

## Reproduce automated checks (PowerShell)

```powershell
Set-Location 'C:\Users\DELL LATITUDE 5410\mathmate-ai\backend'
.\.venv\Scripts\python.exe -m pytest -q
Set-Location 'C:\Users\DELL LATITUDE 5410\mathmate-ai\frontend'
npm.cmd run typecheck
npm.cmd run build
node scripts/test-teacher-performance.mjs
```

## Preview and manual checks

Current preview: http://localhost:3002/app, Learning studio. Click examples or enter a question, select a target if needed, press Solve, then step through results and use Mia's Explain/replay.

Try 3y+5=20 (5), 3n+4=40 (12), 4z-8=12 (5), x^2-5x+6=0 (2 or 3), x²-9=0 (-3 or 3), sqrt(25) (5), 2^5 (32), 1/2+1/3 (5/6), x+y=10 (clarification, then select y for 10-x). Try sin(pi/2) for an explicit unsupported message and 1/0 for division-by-zero feedback.

Check my work: manually confirm 3y+5=20, 3y=15, y=5 (valid); change final line to y=6 (first incorrect step 3). Dropping a root with x²=9 then x=3 is invalid.

To restart the preview, use separate terminals (stop an existing process on these ports before restarting):

```powershell
Set-Location 'C:\Users\DELL LATITUDE 5410\mathmate-ai\backend'
$env:FRONTEND_ORIGIN='http://localhost:3002'
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8002
```

```powershell
Set-Location 'C:\Users\DELL LATITUDE 5410\mathmate-ai\frontend'
$env:BACKEND_URL='http://127.0.0.1:8002'
npm.cmd run dev -- --port 3002
```

A production build uses BACKEND_URL at build time. For production preview, build with that environment variable, then set PORT=3002 and run npm.cmd start.
