# Phase 3A — polynomial calculus milestone

Date: 2026-10-24. Pre-change checkpoint: `412a09d` (verified Phase 2).

This is a bounded first milestone of Phase 3, not completion of all higher mathematics.

## Implemented

- `diff(expression, variable)` for first derivatives.
- `d/dx (expression)` notation (also other supported variable names).
- `integrate(expression, variable)` for indefinite integrals, including one arbitrary real constant C.
- One-variable polynomials of degree at most six, with rational coefficients (integers, fractions and decimals).
- Actual term-by-term power-rule steps. Differentiation is checked against SymPy's derivative; integration is checked by differentiating the computed antiderivative back to the original polynomial.
- Existing 200-character/complexity limits and killable calculation workers remain in effect. The command grammar splits exactly two top-level arguments, validates the variable against the whitelist and uses the shared strict expression parser. No eval, exec or unrestricted string parsing.
- Calculus results use the same solve API, LaTeX rendering and Mia step transcript/chat pipeline.

Examples: diff(x^3,x)=3*x^2; diff(3y^2-2y+7,y)=6*y-2; integrate(x^2,x)=x^3/3+C; integrate(5,n)=5*n+C. An input of degree six may produce an antiderivative of degree seven; degree-seven user input remains outside the existing parser bounds.

## Remaining

Definite integrals, higher derivatives, limits, partial derivatives, symbolic parameter coefficients, trig/log/rational-function calculus, statistics, probability, matrices, vectors and complex-number solving remain for later milestones. Student equation-step checking does not accept calculus command sequences. OCR and real Meta inference are unchanged.

## Files changed

- backend/app/calculus.py (new): strict command grammar, derivative/integral rules and checks.
- backend/app/maths.py: calculus dispatch and explicit step-check boundary.
- backend/app/schemas.py: calculus result kind.
- backend/tests/test_calculus.py (new): correctness, grammar, safety and API/tutor coverage.
- backend/tests/test_general_math.py: now-supported diff/integrate examples moved from negative cases to calculus positive tests.
- frontend/src/lib/types.ts: calculus result kind.
- frontend/src/app/app/page.tsx: calculus examples and guidance.
- docs/math-phase3a.md: this report.

## Local checks

Open http://localhost:3002/app → Learning studio → click diff(x^3, x) or integrate(x^2, x), then step through the power rule and check. Leave Solve for on Auto-detect, or choose the same variable as the command. Try diff(y^2,y) and confirm 2y. Try integrate(1/x,x) and confirm an honest unsupported error.

```powershell
Set-Location 'C:\Users\DELL LATITUDE 5410\mathmate-ai\backend'
.\.venv\Scripts\python.exe -m pytest -q
Set-Location 'C:\Users\DELL LATITUDE 5410\mathmate-ai\frontend'
npm.cmd run typecheck
$env:BACKEND_URL='http://127.0.0.1:8002'
npm.cmd run build
```

Stop a running production frontend before rebuilding on Windows. Preview startup commands remain in math-phase1.md (frontend 3002, backend 8002).

## Verification

- Full backend suite: 162 passed, 1 optional PostgreSQL test skipped, 0 failures (135.74 seconds). Existing Starlette/httpx deprecation warning remains.
- Frontend compilation and build-time TypeScript passed.
- Git whitespace check passed. No lint script is configured.
- Full frontend production build passed; all routes generated successfully.
- Browser: verified diff(x^3,x) produces 3*x^2 with rendered derivative notation; integrate(x^2,x) produces x^3/3+C, with power-rule, arbitrary-constant and differentiation-check steps. Mia renders and its transcript follows the selected calculus step. Audio playback was not retested.
- Screenshot: screenshots/math-phase3a-calculus.jpg.
