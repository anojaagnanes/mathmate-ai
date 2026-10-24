import asyncio
import io
from PIL import Image
from app.config import settings
from app.providers import MetaAIProvider


def test_profile_sessions_and_status(client, auth):
    assert client.put('/api/v1/me', json={'name': '  '}, headers=auth).status_code == 422
    changed = client.put('/api/v1/me', json={'name': '  Ada Lovelace  '}, headers=auth)
    assert changed.json()['name'] == 'Ada Lovelace'
    assert 'password_hash' not in changed.json()
    first = client.post('/api/v1/sessions', json={'lesson_id': 'balance'}, headers=auth)
    second = client.post('/api/v1/sessions', json={'lesson_id': 'balance'}, headers=auth)
    assert first.json()['id'] == second.json()['id']
    assert first.json()['completed'] is False
    assert len(client.get('/api/v1/sessions', headers=auth).json()) == 1
    assert client.post('/api/v1/sessions', json={'lesson_id': 'missing'}, headers=auth).status_code == 404
    assert 'rules' in client.get('/api/v1/recommendations', headers=auth).json()['algorithm']
    status = client.get('/api/v1/tutor/status', headers=auth).json()
    assert status['configured'] is False
    assert 'MODEL_API_KEY' in status['message']


def test_api_output_contracts(client, auth):
    schema = client.get('/openapi.json').json()
    assert schema['paths']['/api/v1/math/solve']['post']['responses']['200']['content']['application/json']['schema']['$ref'].endswith('SolutionOut')
    assert client.post('/api/v1/math/validate', json={'steps': ['x=4', 'x='+'9'*201]}, headers=auth).status_code == 422
    assert client.post('/api/v1/math/validate', json={'steps': ['x=4', '  ']}, headers=auth).status_code == 422


def test_uploaded_image_mime_and_ownership(client, auth):
    image = io.BytesIO()
    Image.new('RGB', (64, 64)).save(image, format='PNG')
    assert client.post('/api/v1/handwriting/upload', files={'file': ('fake.jpg', image.getvalue(), 'image/jpeg')}, headers=auth).status_code == 422
    uploaded = client.post('/api/v1/handwriting/upload', files={'file': ('work.png', image.getvalue(), 'image/png')}, headers=auth).json()
    other = client.post('/api/v1/auth/register', json={'name': 'Other', 'email': 'contracts@example.com', 'password': 'A-long-test-password'}).json()
    headers = {'Authorization': 'Bearer ' + other['access_token']}
    assert client.post('/api/v1/handwriting/'+uploaded['id']+'/confirm', json={'steps': ['x=4']}, headers=headers).status_code == 404
    assert client.get('/api/v1/sessions', headers=headers).json() == []
    path = '/api/v1/handwriting/'+uploaded['id']+'/confirm'
    assert client.post(path, json={'steps': ['2x+3=11', '2x=11']}, headers=auth).json()['error_code'] == 'one_side_changed'
    assert client.post(path, json={'steps': ['x=4']}, headers=auth).status_code == 409
    assert client.get('/api/v1/progress', headers=auth).json()['error_categories'] == {'one_side_changed': 1}


def test_submitted_quiz_cannot_change_hint_history(client, auth):
    q = client.post('/api/v1/quizzes', headers=auth).json()
    client.post('/api/v1/quizzes/'+q['id']+'/submit', json={'answer': '999'}, headers=auth)
    assert client.post('/api/v1/quizzes/'+q['id']+'/hint', headers=auth).status_code == 409
    assert client.get('/api/v1/progress', headers=auth).json()['hints'] == 0


def test_meta_transcription_contract(monkeypatch):
    """Stubbed provider output; this is not a live Meta integration test."""
    captured = {}
    async def request(self, messages, response_format=None):
        captured['messages'] = messages
        captured['format'] = response_format
        return '{"steps":["2x+3=11","2x=8","x=4"]}'
    monkeypatch.setattr(MetaAIProvider, 'request', request)
    steps = asyncio.run(MetaAIProvider().transcribe(b'fixture', 'image/png'))
    assert steps[-1] == 'x=4'
    assert captured['format']['type'] == 'json_schema'
    assert captured['messages'][1]['content'][1]['image_url']['url'].startswith('data:image/png;base64,')


def test_provider_failure_is_explicit_fallback(client, auth, monkeypatch):
    monkeypatch.setattr(settings, 'ai_provider', 'meta')
    async def fail(self, message, verified):
        raise RuntimeError('Unavailable provider')
    monkeypatch.setattr(MetaAIProvider, 'explain', fail)
    response = client.post('/api/v1/tutor/chat', json={'equation': '2x+3=11', 'message': 'Help'}, headers=auth)
    assert response.status_code == 200
    assert 'fallback' in response.json()['mode']
    assert response.json()['verified_math']['solution'] == '4'


def test_refresh_cookie_security(client, auth):
    response = client.post('/api/v1/auth/refresh')
    cookie = response.headers['set-cookie'].lower()
    assert 'httponly' in cookie and 'samesite=strict' in cookie
    assert 'path=/api/v1/auth' in cookie
