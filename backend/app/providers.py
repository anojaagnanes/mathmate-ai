"""Meta contract verified against dev.meta.ai docs on 2026-10-23; live calls unverified."""
import base64
import json
from typing import Protocol
import httpx
from pydantic import BaseModel, Field
from .config import settings


class AIProvider(Protocol):
    name: str
    async def explain(self, message: str, verified: dict) -> str: ...
    async def transcribe(self, image: bytes, mime: str) -> list[str]: ...


class MockAIProvider:
    name = 'local development tutor (not AI inference)'

    async def explain(self, message, verified):
        steps = verified['steps']
        if 'why' in message.lower() or 'balance' in message.lower():
            return 'Think of an equation as a balanced scale. Performing the same reversible operation on both sides keeps it balanced. ' + steps[1]['explanation']
        return 'Let’s take this one step at a time. ' + ' '.join(s['explanation'] for s in steps[1:])

    async def transcribe(self, image, mime):
        return []


class Transcription(BaseModel):
    steps: list[str] = Field(max_length=30)


class MetaAIProvider:
    name = 'Meta AI explanation (generated; refer to verified maths)'

    async def request(self, messages, response_format=None):
        if not settings.model_api_key:
            raise RuntimeError('MODEL_API_KEY is not configured.')
        payload = {'model': settings.meta_model, 'messages': messages, 'max_completion_tokens': 1200}
        if response_format:
            payload['response_format'] = response_format
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post('https://api.meta.ai/v1/chat/completions', headers={'Authorization': f'Bearer {settings.model_api_key}'}, json=payload)
            response.raise_for_status()
            content = response.json()['choices'][0]['message']['content']
            if not isinstance(content, str) or len(content) > 12000:
                raise ValueError('Invalid provider output.')
            return content

    async def explain(self, message, verified):
        return await self.request([{'role': 'developer', 'content': 'You are a kind maths teacher. Explain only the supplied deterministically verified linear equation steps. Do not invent equations, results or claim verification of your prose. Keep your answer under 150 words. Verified data: ' + json.dumps(verified)}, {'role': 'user', 'content': message}])

    async def transcribe(self, image, mime):
        schema = {'type': 'object', 'properties': {'steps': {'type': 'array', 'items': {'type': 'string'}}}, 'required': ['steps'], 'additionalProperties': False}
        result = await self.request([{'role': 'developer', 'content': 'Transcribe handwritten equations in reading order. Do not solve, correct, or invent missing text. Mark unreadable text with ?. Return an empty list if no equations are visible.'}, {'role': 'user', 'content': [{'type': 'text', 'text': 'Transcribe this work for student review.'}, {'type': 'image_url', 'image_url': {'url': f'data:{mime};base64,' + base64.b64encode(image).decode()}}]}], {'type': 'json_schema', 'json_schema': {'name': 'transcription', 'strict': True, 'schema': schema}})
        transcription = Transcription.model_validate_json(result)
        if any(len(step) > 200 for step in transcription.steps):
            raise ValueError('Transcription too long.')
        return transcription.steps


def get_provider() -> AIProvider:
    return MetaAIProvider() if settings.ai_provider == 'meta' else MockAIProvider()
