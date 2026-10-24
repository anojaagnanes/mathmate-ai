import io
from PIL import Image
from app.maths import solve


def test_auth_rotation_logout(client, auth):
    assert client.get('/api/v1/me', headers=auth).status_code == 200
    old = client.cookies.get('mathmate_refresh')
    rotated = client.post('/api/v1/auth/refresh')
    assert rotated.status_code == 200
    assert client.cookies.get('mathmate_refresh') != old
    access = {'Authorization': 'Bearer ' + rotated.json()['access_token']}
    assert client.post('/api/v1/auth/logout').status_code == 200
    assert client.get('/api/v1/me', headers=access).status_code == 401
    assert client.get('/api/v1/me', headers=auth).status_code == 401


def test_refresh_replay_invalidates_family(client, auth):
    old = client.cookies.get('mathmate_refresh')
    new = client.post('/api/v1/auth/refresh').json()['access_token']
    client.cookies.clear()
    client.cookies.set('mathmate_refresh', old)
    assert client.post('/api/v1/auth/refresh').status_code == 401
    assert client.get('/api/v1/me', headers={'Authorization': 'Bearer ' + new}).status_code == 401


def test_login_and_csrf(client, auth):
    assert client.post('/api/v1/auth/login', json={'email': 'ada@example.com', 'password': 'bad'}).status_code == 401
    assert client.post('/api/v1/auth/login', json={'email': 'ada@example.com', 'password': 'Long-password-123'}).status_code == 200
    assert client.post('/api/v1/auth/refresh', headers={'Origin': 'https://evil.example'}).status_code == 403
    assert client.get('/api/v1/progress').status_code == 401
    assert client.post('/api/v1/auth/register', json={'name': 'A', 'email': 'bad', 'password': 'short'}).status_code == 422


def test_end_to_end_api_persistence(client, auth):
    assert client.get('/api/v1/topics', headers=auth).json()[0]['lessons']
    solution = client.post('/api/v1/math/solve', json={'equation': '2x+3=11'}, headers=auth).json()
    assert solution['solution'] == '4'
    assert client.post('/api/v1/lessons/balance/complete', headers=auth).status_code == 200
    for _ in range(5):
        q = client.post('/api/v1/quizzes', headers=auth).json()
        assert 'solution' not in q
        submitted = client.post('/api/v1/quizzes/'+q['id']+'/submit', json={'answer': solve(q['equation'])['solution']}, headers=auth)
        assert submitted.status_code == 200, submitted.text
        assert submitted.json()['correct']
    assert submitted.json()['difficulty'] == 2
    assert client.post('/api/v1/quizzes/'+q['id']+'/submit', json={'answer': '1'}, headers=auth).status_code == 409
    image = io.BytesIO()
    Image.new('RGB', (64, 64), 'white').save(image, format='PNG')
    upload = client.post('/api/v1/handwriting/upload', files={'file': ('work.png', image.getvalue(), 'image/png')}, headers=auth)
    assert upload.status_code == 200, upload.text
    assert upload.json()['mode'] == 'manual' and upload.json()['steps'] == []
    confirmation = client.post('/api/v1/handwriting/'+upload.json()['id']+'/confirm', json={'steps': ['2x+3=11','2x=8','x=5']}, headers=auth)
    assert confirmation.json()['first_incorrect_step'] == 3
    progress = client.get('/api/v1/progress', headers=auth).json()
    assert progress['attempts'] == 5 and progress['correct'] == 5
    assert progress['completed_lessons'] == ['balance']
    assert progress['reviews'][0]['first_incorrect_step'] == 3
    assert client.put('/api/v1/settings', json={'muted': True, 'voice': 'test'}, headers=auth).status_code == 200
    assert client.get('/api/v1/settings', headers=auth).json()['muted']
    chat = client.post('/api/v1/tutor/chat', json={'equation': '2x+3=11', 'message': 'Why?'}, headers=auth)
    assert 'not AI inference' in chat.json()['mode']


def test_ownership(client, auth):
    q = client.post('/api/v1/quizzes', headers=auth).json()
    other = client.post('/api/v1/auth/register', json={'name': 'Other', 'email': 'other@example.com', 'password': 'Long-password-456'}).json()
    headers = {'Authorization': 'Bearer ' + other['access_token']}
    assert client.post('/api/v1/quizzes/'+q['id']+'/submit', json={'answer': '4'}, headers=headers).status_code == 404
    assert client.post('/api/v1/quizzes/'+q['id']+'/hint', headers=headers).status_code == 404
    assert client.get('/api/v1/progress', headers=headers).json()['attempts'] == 0


def test_validation_and_uploads(client, auth):
    assert client.post('/api/v1/math/solve', json={'equation': 'x/0=2'}, headers=auth).status_code == 422
    assert client.post('/api/v1/math/solve', json={'equation': 'x'*201}, headers=auth).status_code == 422
    assert client.post('/api/v1/math/validate', json={'steps': []}, headers=auth).status_code == 422
    assert client.post('/api/v1/handwriting/upload', files={'file': ('bad.png', b'not a picture', 'image/png')}, headers=auth).status_code == 422
    assert client.post('/api/v1/handwriting/upload', files={'file': ('bad.svg', b'<svg/>', 'image/svg+xml')}, headers=auth).status_code == 422
    assert client.post('/api/v1/handwriting/upload', files={'file': ('big.png', b'x'*(5*1024*1024+1), 'image/png')}, headers=auth).status_code == 413
    assert client.post('/api/v1/math/graph', json={'slope': 2, 'intercept': 4}, headers=auth).json()['x_intercept'] == -2
    assert client.post('/api/v1/math/graph', json={'slope': 21, 'intercept': 4}, headers=auth).status_code == 422


def test_hint_recording_and_incorrect_answer(client, auth):
    q = client.post('/api/v1/quizzes', headers=auth).json()
    assert client.post('/api/v1/quizzes/'+q['id']+'/hint', headers=auth).status_code == 200
    result = client.post('/api/v1/quizzes/'+q['id']+'/submit', json={'answer': '999'}, headers=auth).json()
    assert not result['correct']
    p = client.get('/api/v1/progress', headers=auth).json()
    assert p['hints'] == 1 and p['correct'] == 0
