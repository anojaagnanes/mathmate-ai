"""Meta flavor text: silent fallback without Meta, wired wording with it."""
import asyncio


class StubProvider:
    name = 'Stub'

    def __init__(self, calls, text='CANNED WORDS'):
        self.calls = calls
        self.text = text

    async def flavor(self, kind, context):
        self.calls.append((kind, context))
        return self.text


class BoomProvider:
    name = 'Boom'

    async def flavor(self, kind, context):
        raise RuntimeError('quota exhausted')


def solve_answer(client, auth, equation):
    response = client.post('/api/v1/math/solve', json={'equation': equation}, headers=auth)
    assert response.status_code == 200, response.text
    return response.json()['solution']


def answer_mission_correctly(client, auth, mission_id):
    current = client.get('/api/v1/mission/current', headers=auth).json()['current']
    if current['kind'] == 'spot_mistake':
        review = client.post('/api/v1/work/review', json={'steps': current['steps']}, headers=auth)
        assert review.status_code == 200, review.text
        return client.post(f'/api/v1/mission/{mission_id}/answer', json={'answer': str(review.json()['first_incorrect_step'])}, headers=auth).json()
    return client.post(f'/api/v1/mission/{mission_id}/answer', json={'answer': solve_answer(client, auth, current['equation'])}, headers=auth).json()


def test_flavor_falls_back_silently():
    from app.providers import MockAIProvider, flavor_or_empty
    assert asyncio.run(MockAIProvider().flavor('mission_brief', 'goal')) == ''
    assert asyncio.run(flavor_or_empty(BoomProvider(), 'mission_brief', 'goal')) == ''
    assert asyncio.run(flavor_or_empty(object(), 'mission_brief', 'goal')) == ''


def test_endpoints_work_without_meta(client, auth):
    mission = client.post('/api/v1/mission/start', headers=auth).json()
    assert mission['briefing'] is None
    question = client.post('/api/v1/quizzes?topic_id=equations', headers=auth).json()
    wrong = client.post(f"/api/v1/quizzes/{question['id']}/submit", json={'answer': '999999'}, headers=auth).json()
    assert wrong['correct'] is False and wrong['cheer'] is None
    journey = client.post('/api/v1/journey/start', headers=auth).json()
    assert journey['story'] is None
    hint = client.post(f"/api/v1/journey/{journey['id']}/lifeline", json={'kind': 'hint'}, headers=auth).json()
    assert hint['text'] == journey['current']['hint']
    summary = client.get('/api/v1/progress/summary', headers=auth).json()
    assert 'explored' in summary['summary']


def test_meta_words_flow_into_every_surface(client, auth, monkeypatch):
    import app.main as main
    calls = []
    monkeypatch.setattr(main, 'get_provider', lambda session='': StubProvider(calls))
    mission = client.post('/api/v1/mission/start', headers=auth).json()
    assert mission['briefing'] == 'CANNED WORDS'
    assert ('mission_brief', mission['goal'] + ' Topic: ' + mission['topic'] + '.') in calls
    mission_id = mission['id']
    turn = None
    for _ in range(3):
        turn = answer_mission_correctly(client, auth, mission_id)
    assert turn['state'] == 'complete' and turn['cheer'] == 'CANNED WORDS'
    question = client.post('/api/v1/quizzes?topic_id=equations', headers=auth).json()
    wrong = client.post(f"/api/v1/quizzes/{question['id']}/submit", json={'answer': '999999'}, headers=auth).json()
    assert wrong['cheer'] == 'CANNED WORDS'
    journey = client.post('/api/v1/journey/start', headers=auth).json()
    assert journey['story'] == 'CANNED WORDS'
    hint = client.post(f"/api/v1/journey/{journey['id']}/lifeline", json={'kind': 'hint'}, headers=auth).json()
    assert hint['text'] == 'CANNED WORDS'
    journey_id = journey['id']
    turn = None
    for _ in range(3):
        current = client.get('/api/v1/journey/current', headers=auth).json()['current']
        turn = client.post(f'/api/v1/journey/{journey_id}/answer', json={'answer': solve_answer(client, auth, current['equation'])}, headers=auth).json()
    assert turn['event'].startswith('conquered:') and turn['story'] == 'CANNED WORDS'
    summary = client.get('/api/v1/progress/summary', headers=auth).json()
    assert summary['summary'] == 'CANNED WORDS'
    assert {kind for kind, _ in calls} == {'mission_brief', 'mission_cheer', 'quiz_cheer', 'journey_story', 'hint', 'progress'}
