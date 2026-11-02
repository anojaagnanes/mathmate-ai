# Mia: 3D teacher asset and narration

## Model provenance

- Original: Microsoft Rocketbox `Female_Adult_07`, https://github.com/microsoft/Microsoft-Rocketbox
- License: MIT, Copyright (c) 2020 Microsoft. Full notice ships with the model at `frontend/public/models/mia/ROCKETBOX-LICENSE.md`.
- GLB conversion: https://github.com/927tanmay/react-ai-voice-avatar/tree/b984488059717e508bca2979d82cbe8b61916125/assets/avatars
- Source filename: `ananya.glb`; copied unchanged to `teacher.glb`. Conversion provenance notice is included alongside it.
- SHA-256: `da87409e17292434ce468113888e40e1ce2259ccfe27214a775f8b1cd58066dd`
- Size: 4,480,100 bytes. Embedded textures, skinned geometry, humanoid skeleton, 67 named facial targets. No runtime CDN, account or paid avatar service.

## Implementation

React Three Fiber loads the GLB through Three.js GLTFLoader. A cloned skeleton keeps scene instances independent. Studio lighting, upper-body camera, breathing, small head motions, blinking, smiles and approximate jaw motion are procedural. Reduced-motion preference disables idle motion and blinking; speaking still moves the mouth. No animation/video is passed off as geometry.

States: idle, listening (text-field focus, not microphone recording), thinking (pending chat/provider), explaining, encouraging, correct, incorrect, confused and paused. Quiz results come from the deterministic backend. Correct/incorrect reactions use supportive phrases. Lessons highlight the board while narration is active; switching steps cancels old narration. The student chooses when to advance, allowing time for understanding.

## Voice limitations and extension

Browser voice metadata has no gender field. The selector lists English voices and supports preview and explicit preference saving. Existing saved preferences are respected. Clara is Mia's default English voice when available and no valid saved English voice is selected; Microsoft Zira is the fallback. This mapping is supported by Microsoft’s voice documentation: https://learn.microsoft.com/en-us/uwp/api/windows.media.speechsynthesis.voiceinformation.gender . Other unidentified voices require manual selection. The user should preview naturalness and warmth; browser playback events cannot prove subjective audio quality. Rate is 0.88, or 0.78 for slower explanation. Pitch is unaltered.

The mouth animation is a speech-state envelope, NOT phoneme/viseme-accurate lip synchronization. Naturalness is limited by the installed browser/OS voices and the legacy model's mesh and facial rig.

`frontend/src/lib/voice-provider.ts` defines the optional `VoiceProvider` interface and `ServerVoiceProvider` adapter. A developer can pass `voiceProvider` to `Teacher`. The adapter posts text/rate/voice to a same-origin server route and accepts audio. It supports abort, playback, pause/resume and object-URL cleanup in Teacher. It does not implement or enable any vendor service. Implement an authenticated server route using the chosen provider's current official API, keep credentials server-side, enforce user access and text/rate limits, then configure the adapter. No secrets belong in NEXT_PUBLIC variables. No paid API has been purchased or called. Remote audio currently uses the same approximate mouth envelope, not timing data.

## Local verification

Run the backend and frontend as described in README. Open the learning studio, choose a voice, preview it, press Explain / replay, pause/resume/stop, mute, and advance with I understand. In Practice & grow, submit a correct and incorrect answer and observe Mia's response. Check reduced-motion in your OS/browser and a narrow screen. Unsupported WebGL/model errors leave lessons and captions usable.

The renderer corrects legacy metallic material defaults for skin/fabric and initializes cloned skeleton matrices before measuring the model. Run `node scripts/inspect-avatar.mjs` from frontend to validate geometry, facial deformation targets and the scale regression.
