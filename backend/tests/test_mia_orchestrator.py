from app.models import TutorSession, TutorTurn


def _session(client, auth, language='en', question='2x+3=11'):
    r = client.post('/api/v1/tutor/session', json={'language': language, 'mode': 'classroom', 'question': question}, headers=auth)
    assert r.status_code == 200, r.text
    return r.json()


def test_mia_solve_new_question(client, auth):
    s = _session(client, auth)
    r = client.post('/api/v1/tutor/turn', json={'session_id': s['id'], 'message': 'Teach me', 'equation': '3x+5=20'}, headers=auth)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body['verified_math']['verified'] is True
    assert body['whiteboard'], 'whiteboard must carry maths steps'
    assert all('equation' in w for w in body['whiteboard'])
    assert body['plan'], 'orchestrator must expose its plan'
    assert body['followups'], 'orchestrator must suggest follow-ups'


def test_mia_followup_uses_memory(client, auth):
    s = _session(client, auth)
    r1 = client.post('/api/v1/tutor/turn', json={'session_id': s['id'], 'message': 'Teach me', 'equation': '2x+3=11'}, headers=auth)
    assert r1.status_code == 200
    r2 = client.post('/api/v1/tutor/turn', json={'session_id': s['id'], 'message': 'Why does this step work?'}, headers=auth)
    assert r2.status_code == 200, r2.text
    body = r2.json()
    assert body['intent'] == 'followup'
    assert body['verified_math']['verified'] is True
    h = client.get(f"/api/v1/tutor/session/{s['id']}/history", headers=auth)
    assert h.status_code == 200, h.text
    turns = h.json()['turns']
    assert len(turns) >= 4
    assert turns[0]['role'] == 'user'


def test_mia_slow_tamil_and_method(client, auth):
    s = _session(client, auth, language='ta')
    r = client.post('/api/v1/tutor/turn', json={'session_id': s['id'], 'message': 'Explain slowly', 'equation': '2x+3=11', 'slow': True, 'method': 'alternative', 'language': 'ta'}, headers=auth)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body['language'] == 'ta'
    assert body['voice_rate'] == 0.65
    assert body['verified_math']['verified'] is True


def test_mia_practice_and_real_world(client, auth):
    s = _session(client, auth)
    rp = client.post('/api/v1/tutor/turn', json={'session_id': s['id'], 'message': 'Give me practice', 'equation': '1/2+1/4'}, headers=auth)
    assert rp.status_code == 200, rp.text
    assert rp.json()['intent'] == 'practice'
    rw = client.post('/api/v1/tutor/turn', json={'session_id': s['id'], 'message': 'Show a real-world example', 'equation': '2x+3=11'}, headers=auth)
    assert rw.status_code == 200, rw.text
    assert rw.json()['real_world']


def test_mia_voice_config(client, auth):
    r = client.get('/api/v1/tutor/voice', headers=auth)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body['tts'] == 'browser'
    assert 'ta' in body['languages']
    assert body['rates']['slow'] == 0.65


def test_mia_invalid_image_rejected(client, auth):
    s = _session(client, auth)
    r = client.post('/api/v1/tutor/turn', json={'session_id': s['id'], 'message': 'Check this', 'image_base64': 'not-base64!!!', 'image_mime': 'image/png'}, headers=auth)
    assert r.status_code == 200, r.text
    assert r.json()['intent'] == 'transcribe'


def test_legacy_chat_uses_orchestrator(client, auth):
    r = client.post('/api/v1/tutor/chat', json={'equation': '2x+3=11', 'message': 'Why balance?'}, headers=auth)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body['verified_math']['verified'] is True
    assert body['message']
