# Mia — free expression and gesture refinement

This revision keeps the existing licensed female GLB and the current application. No paid service was enabled. Authentication, database, maths solving and handwriting code were not edited.

## Changes

- Warmer resting smile, cheek lift, softer brows, gentler skin normal-map shading and distinct reassurance/celebration expressions.
- Slower arm transitions, reduced arm lifts and finger curls, and wrist rotation limited to 0.7 radians from the authored rest pose to avoid extreme twisting.
- Open-hand, pointing, counting and small celebration targets; quiet intervals and return to rest. Speech gestures follow narration progress. These are procedural approximations, not motion-capture clips; finger counting and pointing are not exact screen-target tracking.
- Replaced the repeating jaw oscillator with named viseme blendshapes. Browser word boundaries restart an English spelling-based estimate for each word. Captions highlight the reported word. Pause, stop, cancellation and lesson changes stop articulation.
- Optional provider path accepts actual viseme intervals and samples them against HTMLAudioElement.currentTime. Pauses, seeks, buffering and silence do not use a separate drifting animation clock.

## Exact timing versus fallback

The current working browser voice is explicitly labeled `word-aligned estimate` (or `estimated visemes` if boundary events are missing). Spelling is not phonetic transcription, so this cannot deliver perfect lip sync. Microsoft Zira remains available without a paid API.

For a future configured provider, VoiceProvider.synthesize may return either a Blob (legacy approximate mode), or `{audio: Blob, cues: [{start: 0.1, end: 0.2, viseme: 'PP'}], language: 'en-US'}`. Times are seconds in the exact returned audio; cues must be ordered and non-overlapping. Supported names: sil, PP, FF, TH, DD, kk, CH, SS, nn, RR, aa, E, I, O, U. The example is a schema illustration, not real timing data.

ServerVoiceProvider also accepts a same-origin JSON response `{audioBase64, mimeType, cues, language}`. No such server endpoint or vendor service has been enabled. A future server implementation must authenticate requests and keep vendor credentials server-side. Map provider phoneme/viseme IDs and units to this contract; do not send guessed timings as provider data. Azure documents audio-offset ticks at https://learn.microsoft.com/en-us/azure/cognitive-services/speech-service/how-to-speech-synthesis-viseme ; browser boundaries are documented at https://developer.mozilla.org/en-US/docs/Web/API/SpeechSynthesisUtterance/boundary_event .

The cue format can accommodate Tamil from a compatible provider. Tamil voice generation and pronunciation have not been implemented or verified; English spelling guesses are not applied to Tamil provider text.

## Verified results

- Final production webpack build and TypeScript compilation passed.
- Six focused timing/performance tests passed (`node scripts/test-teacher-performance.mjs`, Node 24). They cover audio-clock sampling, pause/seek/end, malformed cue rejection, word-boundary resets, Tamil cue transport and finite gesture selection.
- Rig validation passed (`node scripts/inspect-avatar.mjs`), including real facial deformations and articulated finger bones.
- Browser preview loads the 3D model, enters the speaking state, highlights spoken words and accepts Stop. Counting poses were inspected during the earlier refinement; extreme wrist/finger ranges were then reduced. The full final gesture sequence and subjective lip accuracy have not been exhaustively visually verified.
- Tests emit a harmless Node module-type warning. Existing R3F/Three clock deprecation warning remains.
- No backend source changes; backend tests were not rerun for this frontend-only refinement.

## Try it

Open http://localhost:3002/app for this workspace preview. Choose Learning studio, a lesson, and Explain / replay. Listen with Zira, watch the highlighted word and mouth shapes, pause/resume, then Stop. Select a different step and replay. In Practice & grow, correct answers trigger a smile/small celebration and incorrect answers use a reassuring expression. Reduced-motion preference disables idle/gesture movement while retaining speech articulation.

## Changed source files across this refinement

- frontend/src/components/teacher-avatar.tsx
- frontend/src/components/teacher.tsx
- frontend/src/lib/lip-sync.ts (new)
- frontend/src/lib/teacher-performance.ts (new)
- frontend/src/lib/voice-provider.ts
- frontend/src/app/app/page.tsx (passes lesson step number only)
- frontend/scripts/test-teacher-performance.mjs (new)
- frontend/scripts/inspect-avatar.mjs

The original avatar binary is unchanged. Screenshots are under docs/screenshots/mia-*.jpg. Earlier ZIP files are retained; the current source snapshot is dist/mathmate-ai-mia-refined.zip.
