"""Adapter/route contracts use stubbed HTTP; they do not measure recognition quality."""
import asyncio
import base64
import io
import json

import httpx
import pytest
from PIL import Image
from app.config import settings
from app import local_vision as vision


def picture():
    data = io.BytesIO()
    Image.new('RGB', (64, 64), 'white').save(data, format='PNG')
    return data.getvalue()


def stub(monkeypatch, content='{"steps":["3n+4=40"]}', *, status=200, remote=False, done=True, reason='stop'):
    captured = []
    real_client = httpx.AsyncClient
    def handler(request):
        assert request.url.host == '127.0.0.1' and request.url.port == 11434
        body = json.loads(request.content)
        captured.append(body)
        assert body['model'] == vision.MODEL
        if request.url.path == '/api/show':
            return httpx.Response(status, json={'capabilities': ['vision'], 'remote_model': 'cloud-model' if remote else None})
        assert request.url.path == '/api/chat'
        return httpx.Response(200, json={'done': done, 'done_reason': reason, 'message': {'content': content}})
    monkeypatch.setattr(vision.httpx, 'AsyncClient', lambda **kwargs: real_client(transport=httpx.MockTransport(handler), **kwargs))
    return captured


def test_local_contract_and_image_only_payload(monkeypatch):
    calls = stub(monkeypatch)
    assert asyncio.run(vision.OllamaVisionProvider().transcribe(picture(), 'image/png')) == ['3n+4=40']
    payload = calls[-1]
    assert payload['stream'] is False and payload['options']['temperature'] == 0
    assert payload['format']['properties']['steps']['maxItems'] == 30
    assert '3n+4=40' not in str(payload)  # Never give the recognizer the expected answer.
    image = Image.open(io.BytesIO(base64.b64decode(payload['messages'][1]['images'][0])))
    assert image.size == (64, 64)


@pytest.mark.parametrize('content', ['not json', '{"steps":[42]}', '{"steps":[""]}', '{"steps":["' + 'x'*201 + '"]}', '{"steps":[],"answer":12}'])
def test_invalid_output_is_unavailable(monkeypatch, content):
    stub(monkeypatch, content)
    with pytest.raises(vision.VisionUnavailable, match='usable transcription'):
        asyncio.run(vision.OllamaVisionProvider().transcribe(picture(), 'image/png'))


def test_empty_image_text_is_not_invented(monkeypatch):
    stub(monkeypatch, '{"steps":[]}')
    assert asyncio.run(vision.OllamaVisionProvider().transcribe(picture(), 'image/png')) == []


@pytest.mark.parametrize('kwargs,message', [({'status':404}, 'not installed'), ({'remote':True}, 'not a local vision'), ({'done':False}, 'usable transcription'), ({'reason':'length'}, 'usable transcription')])
def test_unavailable_and_truncated_models(monkeypatch, kwargs, message):
    stub(monkeypatch, **kwargs)
    with pytest.raises(vision.VisionUnavailable, match=message):
        asyncio.run(vision.OllamaVisionProvider().transcribe(picture(), 'image/png'))


def test_busy_local_model_does_not_queue():
    async def run():
        async with vision._inference_lock:
            with pytest.raises(vision.VisionUnavailable, match='busy'):
                await vision.OllamaVisionProvider().transcribe(picture(), 'image/png')
    asyncio.run(run())


def test_local_draft_requires_review_before_solve(client, auth, monkeypatch):
    monkeypatch.setattr(settings, 'vision_provider', 'ollama')
    stub(monkeypatch)
    result = client.post('/api/v1/math/question', headers=auth, files={'file': ('work.png', picture(), 'image/png')}).json()
    assert result['status'] == 'review_required' and result['solution'] is None
    assert result['upload']['steps'] == ['3n+4=40']
    assert 'Review every line' in result['message']
    solved = client.post('/api/v1/math/question', headers=auth, data={'question':result['upload']['steps'][0]}).json()
    assert solved['solution']['solution'] == '12' and solved['solution']['verified']


def test_missing_model_route_retains_actionable_message(client, auth, monkeypatch):
    monkeypatch.setattr(settings, 'vision_provider', 'ollama')
    stub(monkeypatch, status=404)
    result = client.post('/api/v1/math/question', headers=auth, files={'file': ('work.png', picture(), 'image/png')}).json()
    assert result['status'] == 'manual_required' and result['solution'] is None
    assert 'not installed' in result['message']
