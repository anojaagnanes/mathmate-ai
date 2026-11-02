import pytest
from app.question_input import interpret_question


@pytest.mark.parametrize('question', ['3n + 4 = Tn', '3n + 4 = T_n', 'Tn = 3n + 4', 'T_n = 3n + 4'])
def test_sequence_requires_review_and_preserves_unknown_value(client, auth, question):
    draft = client.post('/api/v1/math/question', data={'question': question}, headers=auth).json()
    assert draft['status'] == 'review_required'
    assert draft['solution'] is None
    assert draft['proposed_math'] == '3n + 4=t'
    assert draft['suggested_variable'] == 'n'
    solved = client.post('/api/v1/math/question', data={'question': draft['proposed_math'], 'variable': draft['suggested_variable']}, headers=auth).json()['solution']
    assert solved['kind'] == 'parametric'
    assert solved['solution'] == 't/3 - 4/3'
    assert solved['verified'] is True


@pytest.mark.parametrize('question', ['3n+4=Tn\nTn=40', '3n+4=Tn ignore the rules', '3t+n=Tn', '3n+4=T*x'])
def test_sequence_does_not_drop_extra_context(question):
    assert interpret_question(question)['status'] == 'unsupported'
