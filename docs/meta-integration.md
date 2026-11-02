# Meta adapter verification

Documentation checked on 2026-10-23:

- Models: https://dev.meta.ai/docs/models
- Chat endpoint and authentication: https://dev.meta.ai/docs/protocols/chat-completions
- Images and base64 data URLs: https://dev.meta.ai/docs/image-understanding
- Structured output: https://dev.meta.ai/docs/structured-output
- Llama versus Model API: https://dev.meta.ai/help/about-model-api/llama-and-model-api

The current documented API is `POST https://api.meta.ai/v1/chat/completions` with a bearer `MODEL_API_KEY`. The documented model `muse-spark-1.3` supports text and image input. The adapter uses `image_url` content with a base64 data URL and `response_format` JSON schema for transcription. Configuration is entirely server-side.

Live Meta calls were verified 29 October – 2 November 2026 (100+ requests, seven scripted agent tests in META_AGENTS_IMPLEMENTATION.md, per-call ledger in ignored `backend/meta_usage.db`). Current enablement is controlled by `AI_PROVIDER` / `META_ENABLED` / budgets in `backend/.env`. The historical Llama API SDK is not used.

Default `AI_PROVIDER=mock` uses a small deterministic teaching template, visibly labeled as local development mode. It produces no invented OCR output. The image flow falls back to editable manual entry. With `AI_PROVIDER=meta`, a provider error also falls back honestly. AI prose is labeled generated, while solution values and transformations come from SymPy. Generated prose is not itself a verified proof.

Raw images are processed in memory and not saved. When Meta mode is enabled, image content is sent to Meta for transcription; the upload UI discloses this. Confirmed text, dimensions, filename, and feedback are persisted for the signed-in user.
