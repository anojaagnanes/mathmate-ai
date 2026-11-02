"""Repeated reviews: lesson self-checks must not save, identical re-submits save once."""


def _reviews(client, auth):
    return client.get('/api/v1/progress', headers=auth).json()['reviews']


def _post_review(client, auth, steps, attempts=3):
    """Worker-backed review; a failed spawn saves nothing, so retry until solved."""
    last = None
    for _ in range(attempts):
        last = client.post('/api/v1/work/review', json={'steps': steps}, headers=auth)
        if last.status_code == 200 and last.json().get('corrected') is not None:
            return last.json()
    raise AssertionError('work review never solved: ' + (last.text if last is not None else 'no response'))


def _post_validate(client, auth, payload, attempts=3):
    last = None
    for _ in range(attempts):
        last = client.post('/api/v1/math/validate', json=payload, headers=auth)
        if last.status_code == 200 and 'valid' in last.json():
            return last.json()
    raise AssertionError('validate never solved: ' + (last.text if last is not None else 'no response'))


def _post_check_work(client, auth, body, attempts=3):
    last = None
    for _ in range(attempts):
        last = client.post('/api/v1/math/question', data=body, headers=auth)
        if last.status_code == 200 and last.json().get('status') == 'solved':
            return last.json()
    raise AssertionError('check_work never solved: ' + (last.text if last is not None else 'no response'))


def test_lesson_verification_writes_no_review(client, auth):
    lesson_steps = ['2x + 6 = 14', '2x = 14 - 6', '2x = 8', 'x = 8 / 2', 'x = 4']
    before = _reviews(client, auth)
    response = _post_validate(client, auth, {'steps': lesson_steps, 'verify_only': True})
    assert response['valid'] is True
    assert _reviews(client, auth) == before
    _post_validate(client, auth, {'steps': lesson_steps})
    assert len(_reviews(client, auth)) == len(before) + 1


def test_work_review_repeat_returns_same_id(client, auth):
    steps = ['2x+6=14', '2x=20', 'x=10']
    first = _post_review(client, auth, steps)
    second = _post_review(client, auth, steps)
    assert second['id'] == first['id']
    assert len(_reviews(client, auth)) == 1
    third = _post_review(client, auth, ['3n+4=40', '3n=36', 'n=12'])
    assert third['id'] != first['id']
    assert len(_reviews(client, auth)) == 2


def test_check_work_repeat_saves_once(client, auth):
    body = {'question': '2x+6=14\n2x=8\nx=4', 'intent': 'check_work'}
    first = _post_check_work(client, auth, body)
    assert first['route'] == 'working'
    _post_check_work(client, auth, body)
    assert len(_reviews(client, auth)) == 1


def test_progress_shows_newest_review_first(client, auth):
    _post_review(client, auth, ['2x+6=14', '2x=20', 'x=10'])
    _post_review(client, auth, ['3n+4=40', '3n=36', 'n=12'])
    reviews = _reviews(client, auth)
    assert len(reviews) == 2
    assert reviews[0]['corrected']['solution'] == '12'
    assert reviews[1]['corrected']['solution'] == '4'
