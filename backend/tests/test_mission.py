"""Autonomous mission loop: diagnose, drill, adapt, verdict. Answers stay server-side."""


def solve_answer(client, auth, equation):
    response = client.post('/api/v1/math/solve', json={'equation': equation}, headers=auth)
    assert response.status_code == 200, response.text
    return response.json()['solution']


def answer_current_correctly(client, auth, mission_id):
    """Answer whatever drill is current, using only public API responses.

    Spot-the-mistake rounds are solved through the production work reviewer,
    proving each served round is genuinely engine-verifiable."""
    current = client.get('/api/v1/mission/current', headers=auth).json()['current']
    if current['kind'] == 'spot_mistake':
        review = client.post('/api/v1/work/review', json={'steps': current['steps']}, headers=auth)
        assert review.status_code == 200, review.text
        wrong_line = review.json()['first_incorrect_step']
        assert wrong_line, review.json()
        return client.post(f'/api/v1/mission/{mission_id}/answer', json={'answer': str(wrong_line)}, headers=auth)
    return client.post(f'/api/v1/mission/{mission_id}/answer',
                       json={'answer': solve_answer(client, auth, current['equation'])}, headers=auth)


def test_mission_diagnoses_top_error_and_reaches_mastery(client, auth):
    bad = client.post('/api/v1/math/validate', json={'steps': ['2x+3=11', '2x=8', 'x=5']}, headers=auth)
    assert bad.status_code == 200 and bad.json()['valid'] is False
    start = client.post('/api/v1/mission/start', headers=auth)
    assert start.status_code == 200, start.text
    body = start.json()
    assert body['error'] == 'changed_solution'
    assert body['state'] == 'active'
    assert body['example']['steps']
    assert 'answer' not in body['current']
    # The worked example is teaching material: its answer is shown on purpose.
    assert body['example']['answer']
    mission_id = body['id']
    # Starting again resumes the same active mission instead of duplicating it.
    again = client.post('/api/v1/mission/start', headers=auth)
    assert again.json()['id'] == mission_id
    turn = None
    for _ in range(3):
        turn = answer_current_correctly(client, auth, mission_id)
        assert turn.status_code == 200, turn.text
        assert turn.json()['correct'] is True
        assert 'answer' not in (turn.json()['current'] or {})
    assert turn.json()['state'] == 'complete'
    assert turn.json()['verdict']['mastered'] is True
    assert 'Mastery achieved' in turn.json()['trace'][-1]
    # A completed mission rejects further answers and reports no active mission.
    assert client.post(f'/api/v1/mission/{mission_id}/answer', json={'answer': '4'}, headers=auth).status_code == 409
    assert client.get('/api/v1/mission/current', headers=auth).status_code == 404


def test_mission_stops_after_three_wrong_with_teaching(client, auth):
    mission_id = client.post('/api/v1/mission/start', headers=auth).json()['id']
    turn = None
    for _ in range(3):
        turn = client.post(f'/api/v1/mission/{mission_id}/answer', json={'answer': '999999'}, headers=auth)
        assert turn.status_code == 200, turn.text
        assert turn.json()['correct'] is False
    body = turn.json()
    assert body['state'] == 'complete'
    assert body['verdict']['mastered'] is False
    assert len(body['verdict']['teaching']) == 3
    assert all(item['answer'] and item['hint'] for item in body['verdict']['teaching'])
    assert 'Three wrong answers' in body['message']
    assert client.post(f'/api/v1/mission/{mission_id}/answer', json={'answer': '999999'}, headers=auth).status_code == 409


def test_mission_replans_before_third_strike(client, auth):
    mission_id = client.post('/api/v1/mission/start', headers=auth).json()['id']

    def answer(value):
        return client.post(f'/api/v1/mission/{mission_id}/answer', json={'answer': value}, headers=auth)

    def current_equation():
        return client.get('/api/v1/mission/current', headers=auth).json()['current']['equation']

    assert answer(solve_answer(client, auth, current_equation())).json()['correct'] is True
    assert answer(solve_answer(client, auth, current_equation())).json()['correct'] is True
    assert answer('999999').json()['correct'] is False
    turn = answer('999999').json()
    assert turn['correct'] is False
    assert any('Re-plan' in line for line in turn['trace'])
    assert turn['difficulty'] == 1
    final = answer('999999').json()
    assert final['state'] == 'complete'
    assert len(final['verdict']['teaching']) == 3


def test_mission_targets_fraction_mistake_from_work_review(client, auth):
    review = client.post('/api/v1/work/review', json={'steps': ['1/2 + 1/4 = 2/6']}, headers=auth)
    assert review.json()['error_category'] == 'fraction_addition'
    body = client.post('/api/v1/mission/start', headers=auth).json()
    assert body['topic'] == 'fractions'
    assert body['error'] == 'fraction_addition'
    mission_id = body['id']
    turn = None
    for _ in range(3):
        turn = answer_current_correctly(client, auth, mission_id)
        assert turn.json()['correct'] is True
    assert turn.json()['state'] == 'complete'
    assert turn.json()['verdict']['mastered'] is True


def test_mission_spot_mistake_round_completes_mastery(client, auth):
    mission_id = client.post('/api/v1/mission/start', headers=auth).json()['id']
    assert answer_current_correctly(client, auth, mission_id).json()['correct'] is True
    turn = answer_current_correctly(client, auth, mission_id).json()
    assert turn['correct'] is True
    current = turn['current']
    assert current['kind'] == 'spot_mistake'
    assert 2 <= len(current['steps']) <= 3
    assert 'answer' not in current and 'wrong_line' not in current and 'explanation' not in current
    assert any('Role reversal' in line for line in turn['trace'])
    final = answer_current_correctly(client, auth, mission_id).json()
    assert final['correct'] is True
    assert final['state'] == 'complete'
    assert final['verdict']['mastered'] is True
    assert 'slip' in final['message']


def test_mission_spot_mistake_wrong_and_malformed(client, auth):
    mission_id = client.post('/api/v1/mission/start', headers=auth).json()['id']
    assert answer_current_correctly(client, auth, mission_id).json()['correct'] is True
    assert answer_current_correctly(client, auth, mission_id).json()['correct'] is True
    current = client.get('/api/v1/mission/current', headers=auth).json()['current']
    assert current['kind'] == 'spot_mistake'
    # Input with no line number is malformed and leaves the mission untouched.
    assert client.post(f'/api/v1/mission/{mission_id}/answer', json={'answer': 'banana'}, headers=auth).status_code == 422
    assert client.get('/api/v1/mission/current', headers=auth).json()['current']['kind'] == 'spot_mistake'
    # A wrong numeric guess is simply incorrect and resets the streak.
    review = client.post('/api/v1/work/review', json={'steps': current['steps']}, headers=auth).json()
    wrong_line = review['first_incorrect_step']
    guess = 1 if wrong_line != 1 else 2
    turn = client.post(f'/api/v1/mission/{mission_id}/answer', json={'answer': str(guess)}, headers=auth).json()
    assert turn['correct'] is False
    assert turn['consecutive'] == 0
    assert turn['state'] == 'active'
    assert f'line {wrong_line}' in turn['message']
    # The role-reversal round appears only once per mission.
    assert sum(1 for line in turn['trace'] if 'Role reversal' in line) == 1


def test_mission_skips_just_mastered_error(client, auth):
    for _ in range(2):
        bad = client.post('/api/v1/work/review', json={'steps': ['1/2 + 1/4 = 2/6']}, headers=auth)
        assert bad.status_code == 200 and bad.json()['error_category'] == 'fraction_addition'
    bad = client.post('/api/v1/math/validate', json={'steps': ['2x+3=11', '2x=8', 'x=5']}, headers=auth)
    assert bad.status_code == 200 and bad.json()['valid'] is False
    first = client.post('/api/v1/mission/start', headers=auth).json()
    assert first['error'] == 'fraction_addition'
    turn = None
    for _ in range(3):
        turn = answer_current_correctly(client, auth, first['id'])
        assert turn.json()['correct'] is True
    assert turn.json()['state'] == 'complete'
    assert turn.json()['verdict']['mastered'] is True
    second = client.post('/api/v1/mission/start', headers=auth).json()
    assert second['error'] != 'fraction_addition'
    assert second['topic'] == 'equations'
    assert any('already mastered' in line for line in second['trace'])


def test_mission_restart_serves_fresh_drills(client, auth):
    first = client.post('/api/v1/mission/start', headers=auth).json()
    asked = {first['example']['equation']}
    turn = None
    for _ in range(3):
        current = client.get('/api/v1/mission/current', headers=auth).json()['current']
        asked.add(current['equation'])
        turn = answer_current_correctly(client, auth, first['id'])
        assert turn.json()['correct'] is True
    assert turn.json()['verdict']['mastered'] is True
    second = client.post('/api/v1/mission/start', headers=auth).json()
    assert second['current']['equation'] not in asked


def test_mission_rejects_bad_input_and_foreign_users(client, auth):
    mission_id = client.post('/api/v1/mission/start', headers=auth).json()['id']
    assert client.post(f'/api/v1/mission/{mission_id}/answer', json={'answer': 'x+1'}, headers=auth).status_code == 422
    other = client.post('/api/v1/auth/register', json={'name': 'Other', 'email': 'mission-other@example.com', 'password': 'Long-password-123'}).json()
    foreign = {'Authorization': 'Bearer ' + other['access_token']}
    assert client.post(f'/api/v1/mission/{mission_id}/answer', json={'answer': '4'}, headers=foreign).status_code == 404
    assert client.post('/api/v1/mission/does-not-exist/answer', json={'answer': '4'}, headers=auth).status_code == 404
