"""Learning Journey: stages, progress, help options, and the final verdict."""
from fractions import Fraction


def solve_answer(client, auth, equation):
    response = client.post('/api/v1/math/solve', json={'equation': equation}, headers=auth)
    assert response.status_code == 200, response.text
    return response.json()['solution']


def fraction_answer(equation):
    import re
    if equation.startswith('Compare'):
        a, b, c, d = (int(x) for x in re.findall(r'\d+', equation)[:4])
        left, right = Fraction(a, b), Fraction(c, d)
        return '<' if left < right else '>' if left > right else '='
    total = Fraction(0)
    for term in equation.split('+'):
        term = term.strip()
        if '/' in term:
            n, d = term.split('/')
            total += Fraction(int(n), int(d))
        else:
            total += Fraction(term)
    return str(total)


def answer_current_correctly(client, auth, journey_id):
    current = client.get('/api/v1/journey/current', headers=auth).json()['current']
    if current['kind'] == 'spot_mistake':
        review = client.post('/api/v1/work/review', json={'steps': current['steps']}, headers=auth)
        assert review.status_code == 200, review.text
        return client.post(f'/api/v1/journey/{journey_id}/answer', json={'answer': str(review.json()['first_incorrect_step'])}, headers=auth)
    if '/' in current['equation']:
        return client.post(f'/api/v1/journey/{journey_id}/answer', json={'answer': fraction_answer(current['equation'])}, headers=auth)
    return client.post(f'/api/v1/journey/{journey_id}/answer', json={'answer': solve_answer(client, auth, current['equation'])}, headers=auth)


def test_journey_sails_all_islands_to_treasure(client, auth):
    start = client.post('/api/v1/journey/start', headers=auth)
    assert start.status_code == 200, start.text
    body = start.json()
    assert [i['title'] for i in body['islands']] == ['Linear equations', 'Adding fractions', 'X-intercepts', 'Equivalent fractions', 'Mixed challenge']
    assert body['islands'][0]['state'] == 'current'
    assert body['current']['difficulty'] == 1
    assert 'answer' not in body['current']
    journey_id = body['id']
    # Restarting resumes the same active voyage.
    assert client.post('/api/v1/journey/start', headers=auth).json()['id'] == journey_id
    events = []
    for _ in range(30):
        turn = answer_current_correctly(client, auth, journey_id)
        assert turn.status_code == 200, turn.text
        assert turn.json()['correct'] is True
        if turn.json()['event']:
            events.append(turn.json()['event'])
        if turn.json()['state'] == 'complete':
            break
    body = turn.json()
    assert body['state'] == 'complete'
    assert body['verdict']['treasure'] is True
    assert body['verdict']['gems'] == 15
    assert all(e.startswith('conquered:') for e in events) and len(events) == 5
    assert 'Journey complete' in body['verdict']['message']
    assert client.post(f'/api/v1/journey/{journey_id}/answer', json={'answer': '4'}, headers=auth).status_code == 409
    assert client.get('/api/v1/journey/current', headers=auth).status_code == 404


def test_journey_restart_abandons_and_starts_fresh(client, auth):
    first = client.post('/api/v1/journey/start', headers=auth).json()['id']
    second = client.post('/api/v1/journey/restart', headers=auth).json()
    assert second['id'] != first
    assert second['state'] == 'active' and len(second['islands']) == 5
    assert second['current'] and second['islands'][0]['gems'] == 0
    assert client.post('/api/v1/journey/start', headers=auth).json()['id'] == second['id']


def test_journey_ramps_easy_to_advanced_within_island(client, auth):
    journey_id = client.post('/api/v1/journey/start', headers=auth).json()['id']
    seen = [client.get('/api/v1/journey/current', headers=auth).json()['current']['difficulty']]
    for _ in range(2):
        turn = answer_current_correctly(client, auth, journey_id)
        assert turn.status_code == 200, turn.text
        if turn.json()['current'] and turn.json()['island_index'] == 0:
            seen.append(turn.json()['current']['difficulty'])
    assert seen == [1, 2, 3]


def test_journey_lifelines_guide_without_grading_by_prose(client, auth):
    journey_id = client.post('/api/v1/journey/start', headers=auth).json()['id']
    hint = client.post(f'/api/v1/journey/{journey_id}/lifeline', json={'kind': 'hint'}, headers=auth)
    assert hint.status_code == 200 and hint.json()['text']
    nudge = client.post(f'/api/v1/journey/{journey_id}/lifeline', json={'kind': 'nudge'}, headers=auth)
    assert nudge.status_code == 200, nudge.text
    assert nudge.json()['step'] and nudge.json()['step']['equation']
    assert nudge.json()['answer'] is None
    reveal = client.post(f'/api/v1/journey/{journey_id}/lifeline', json={'kind': 'reveal'}, headers=auth)
    assert reveal.status_code == 200, reveal.text
    assert reveal.json()['steps'] and reveal.json()['answer']
    # A revealed answer earns no gem but the voyage continues.
    turn = answer_current_correctly(client, auth, journey_id)
    assert turn.json()['correct'] is True
    assert turn.json()['islands'][0]['gems'] == 0
    assert 'does not count' in turn.json()['message']
    assert client.post(f'/api/v1/journey/{journey_id}/lifeline', json={'kind': 'teleport'}, headers=auth).status_code == 422


def current_equation(client, auth):
    return client.get('/api/v1/journey/current', headers=auth).json()['current']['equation']


def test_journey_retries_until_pass_then_teaches(client, auth):
    journey_id = client.post('/api/v1/journey/start', headers=auth).json()['id']
    first = current_equation(client, auth)

    def wrong():
        response = client.post(f'/api/v1/journey/{journey_id}/answer', json={'answer': '999999'}, headers=auth)
        assert response.status_code == 200, response.text
        return response.json()

    # Misses 1-2: same question again, no answer revealed, Next stays locked.
    for attempt in (1, 2):
        turn = wrong()
        assert turn['correct'] is False and turn['advanced'] is False
        assert f'Attempt {attempt} of 3' in turn['message']
        assert 'verified answer is' not in turn['message']
        assert current_equation(client, auth) == first
    # Miss 3: taught the verified answer and moved on.
    turn = wrong()
    assert turn['correct'] is False and turn['advanced'] is True
    assert 'verified answer is' in turn['message']
    second = current_equation(client, auth)
    assert second != first
    # Passing the new question earns a gem and unlocks Next.
    turn = client.post(f'/api/v1/journey/{journey_id}/answer', json={'answer': solve_answer(client, auth, second)}, headers=auth).json()
    assert turn['correct'] is True and turn['advanced'] is True
    assert turn['islands'][0]['gems'] == 1


def test_journey_opens_secret_passage_after_eight_tries(client, auth):
    journey_id = client.post('/api/v1/journey/start', headers=auth).json()['id']
    turn = None
    for _ in range(8):
        response = client.post(f'/api/v1/journey/{journey_id}/answer', json={'answer': '999999'}, headers=auth)
        assert response.status_code == 200, response.text
        turn = response.json()
        assert turn['correct'] is False
    assert turn['event'] == 'passage:Linear equations'
    assert turn['islands'][0]['state'] == 'cursed'
    assert turn['islands'][0]['gems'] == 0
    assert turn['island_index'] == 1
    assert turn['state'] == 'active'
