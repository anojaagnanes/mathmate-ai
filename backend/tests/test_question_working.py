import pytest


@pytest.mark.parametrize('steps,valid,wrong', [
    ('2x+6=14\n2x=8\nx=4', True, None),
    ('2x+6=14\n2x=20\nx=10', False, 2),
    ('3n+4=40\n3n=36\nn=12', True, None),
])
def test_explicit_working_feedback(client, auth, steps, valid, wrong):
    response = client.post('/api/v1/math/question', data={'question': steps, 'intent': 'check_work'}, headers=auth)
    assert response.status_code == 200, response.text
    result = response.json()
    assert result['route'] == 'working' and result['status'] == 'solved'
    assert result['feedback']['valid'] is valid
    assert result['feedback']['first_incorrect_step'] == wrong
    assert result['solution']['verified']
    assert result['solution']['solution'] == ('12' if steps.startswith('3n') else '4')


def test_working_unsupported_is_explicit(client, auth):
    result = client.post('/api/v1/math/question', data={'question': 'Explain a circle', 'intent': 'check_work'}, headers=auth).json()
    assert result['status'] == 'unsupported' and result['solution'] is None
    assert result['message']


def test_default_system_route_preserved(client, auth):
    result = client.post('/api/v1/math/question', data={'question': 'x+y=3\nx-y=1'}, headers=auth).json()
    assert result['route'] == 'solver' and result['solution']['verified']


def test_unknown_intent_rejected(client, auth):
    assert client.post('/api/v1/math/question', data={'question': 'x=4', 'intent': 'invent'}, headers=auth).status_code == 422
