# Advanced maths — Phase 2

Date: 2026-10-24. Phase 1 checkpoint: `4f74de3`. No new dependencies, paid services, schema migrations, database resets or deployment.

## Added

- Two or three simultaneous linear equations, one to three variables, rational coefficients. Separate with semicolons, newlines, or ` with `. Row reduction records actual swap/divide/elimination operations; unique and parametric answers are substituted into every original equation. Contradictory rows identify no solution.
- Single-variable linear and quadratic inequalities over real numbers with rational coefficients. Negative divisors reverse the sign. Quadratic zeros and interval solution sets are shown, including inclusive/exclusive endpoints and empty/all-real cases.
- Constants pi/π and E; single-argument sin, cos, tan, log, exp; symbolic square-root expressions. Angles use radians and log means natural logarithm. Numeric values remain exact where possible; otherwise they remain symbolic.
- Domain conditions are collected before simplification and returned with expressions (for example log(x)-log(x)=0 still requires x>0). Restricted-domain equations remain explicitly unsupported, preventing invalid cancellation from being presented as an unrestricted identity.
- Function graph endpoint and UI preserve the original slope/intercept playground. Curves are rendered from server-computed coordinates, without evaluating student strings in JavaScript or Python. Four hundred and one approximate samples cover the selected interval (UI defaults to -5..5); API intervals are bounded to -10..10. Undefined or clipped points and tangent poles split curves into segments. Isolated real sample points are plotted separately.
- Mia uses the same expanded result schema and current step transcript. No avatar or voice implementation was replaced.

## Limits

This does not implement arbitrary higher maths. Nonlinear systems, variable denominators, complex solutions, calculus, symbolic inequality parameters, chained inequalities and solving trigonometric/logarithmic equations remain unsupported. Inequalities and systems require rational coefficients. Domain-restricted expressions can be simplified or plotted, but not solved as equations. Student transformation checking remains single-variable linear/quadratic equations; system and inequality step sequences are explicitly rejected.

Graph function arguments must be affine in x with slope magnitude at most 10, including functions retained in domain guards after cancellation. All graph outputs are approximate, not exact proofs of continuity. Function values above magnitude 10,000 are omitted. Numeric function arguments have magnitude at most 1000; numeric exp arguments at most 50. Existing strict grammar, length/depth/complexity bounds, eight-second killable workers and four calculation slots per server process remain in effect. No unrestricted sympify, eval, exec or lambdify is used.

No OCR/PDF recognition or live Meta access was added in this maths phase. Existing image transcription/manual confirmation and linear quizzes remain available.

## Changed files

- backend/app/advanced_maths.py (new): systems, inequalities, graph sampling.
- backend/app/math_parser.py: whitelisted functions/constants and domain tracking.
- backend/app/maths.py: dispatch and expression domain metadata.
- backend/app/math_runtime.py: graph operation through the worker boundary.
- backend/app/main.py: authenticated typed graph API.
- backend/app/schemas.py: result kinds, assignments, domain conditions, graph request/response.
- backend/tests/test_advanced_math.py (new): positive, negative, domain, graph and API cases.
- backend/tests/test_general_math.py and test_maths.py: newly supported inputs moved from negative assertions into the new positive suite; remaining security cases retained.
- frontend/src/components/graph.tsx: function plotter alongside original line playground.
- frontend/src/app/app/page.tsx: advanced examples, result summary and domain display.
- frontend/src/lib/types.ts: expanded result contract.
- docs/math-phase2.md (this report).

## Verify locally

Learning studio examples:

| Input | Expected |
|---|---|
| 2x+y=7; x-y=2 | x=3, y=1; substitution into both equations |
| x+y=2; 2x+2y=4 | Infinitely many solutions, expressed with a free variable |
| x+y=2; x+y=3 | No solution |
| -2x+3>7 | x<-2; reversed inequality sign |
| x²-9<=0 | [-3,3] |
| sin(pi/2) | 1 |
| log(E) | 1 |
| log(x)-log(x) | 0, retaining x>0 |

Graph playground: try x², sin(x), tan(x), log(x), sqrt(x), exp(x). Tangent must have separated branches; logarithm must have no nonpositive-x points. The old slope sliders still work.

PowerShell test commands:

```powershell
Set-Location 'C:\Users\DELL LATITUDE 5410\mathmate-ai\backend'
.\.venv\Scripts\python.exe -m pytest -q
Set-Location 'C:\Users\DELL LATITUDE 5410\mathmate-ai\frontend'
npm.cmd run typecheck
$env:BACKEND_URL='http://127.0.0.1:8002'
npm.cmd run build
```

Stop a running production preview before building on Windows to avoid locked standalone files. Startup instructions remain in math-phase1.md. Current preview uses frontend 3002 and backend 8002.

## Automated verification

- Full backend suite: 134 passed, 1 optional PostgreSQL test skipped, 0 failures (123.85 seconds). Existing Starlette/httpx deprecation warning remains.
- Focused maths suite: 114 passed, 4 API/worker tests deselected; those tests were subsequently included in the full suite.
- TypeScript: passed. No lint script is configured.
- Git whitespace check: passed.
- Frontend production build: passed after stopping the running preview that locked the standalone output directory on Windows.
- Browser production preview: verified x=3, y=1 for the example system, with ten row-reduction/substitution steps; verified the negative-divisor inequality reversal and resulting interval; verified the sqrt(x) graph renders with x>=0 domain guidance alongside the existing linear graph and sliders. Tangent branch separation was verified by automated tests; the browser was switched to sqrt(x) during live interaction, so tangent visual inspection was not completed.
- Mia remains rendered and its transcript follows the selected system step. Audio playback was not retested in this phase.
- Screenshots: screenshots/math-phase2-system.jpg and screenshots/math-phase2-graph.jpg.
