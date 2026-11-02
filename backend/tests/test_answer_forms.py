"""Answer forms: children can write x = 4, not just 4, everywhere graded."""


def _solve(client, auth, equation):
    response = client.post('/api/v1/math/solve', json={'equation': equation}, headers=auth)
    assert response.status_code == 200, response.text
    return response.json()['solution']


def test_journey_accepts_variable_equals_value(client, auth):
    start = client.post('/api/v1/journey/start', headers=auth).json()
    equation = start['current']['equation']
    answer = f"x = {_solve(client, auth, equation)}"
    turn = client.post(f"/api/v1/journey/{start['id']}/answer", json={'answer': answer}, headers=auth)
    assert turn.status_code == 200, turn.text
    assert turn.json()['correct'] is True and turn.json()['advanced'] is True


def test_journey_rejects_garbage(client, auth):
    start = client.post('/api/v1/journey/start', headers=auth).json()
    bad = client.post(f"/api/v1/journey/{start['id']}/answer", json={'answer': 'banana'}, headers=auth)
    assert bad.status_code == 422


def test_mission_accepts_variable_equals_value(client, auth):
    seed = client.post('/api/v1/math/validate', json={'steps': ['2x+3=11', '2x=8', 'x=5']}, headers=auth)
    assert seed.json()['valid'] is False
    mission_id = client.post('/api/v1/mission/start', headers=auth).json()['id']
    for _ in range(4):
        current = client.get('/api/v1/mission/current', headers=auth).json()['current']
        if current['kind'] == 'spot_mistake':
            review = client.post('/api/v1/work/review', json={'steps': current['steps']}, headers=auth).json()
            client.post(f'/api/v1/mission/{mission_id}/answer',
                        json={'answer': str(review['first_incorrect_step'])}, headers=auth)
            continue
        answer = f"x = {_solve(client, auth, current['equation'])}"
        result = client.post(f'/api/v1/mission/{mission_id}/answer', json={'answer': answer}, headers=auth)
        assert result.status_code == 200, result.text
        assert result.json()['correct'] is True
        return
    raise AssertionError('no value drill was served')


def test_quiz_accepts_variable_equals_value(client, auth):
    quiz = client.post('/api/v1/quizzes', headers=auth).json()
    answer = f"x = {_solve(client, auth, quiz['equation'])}"
    submitted = client.post(f"/api/v1/quizzes/{quiz['id']}/submit", json={'answer': answer}, headers=auth)
    assert submitted.status_code == 200, submitted.text
    assert submitted.json()['correct'] is True
