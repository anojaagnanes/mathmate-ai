import io
import pytest
from PIL import Image


def image_file(fmt='PNG'):
    stream = io.BytesIO()
    Image.new('RGB', (32, 32), 'white').save(stream, format=fmt)
    return ('question.' + fmt.lower(), stream.getvalue(), {'PNG': 'image/png', 'JPEG': 'image/jpeg', 'WEBP': 'image/webp'}[fmt])


@pytest.mark.parametrize('question,expected', [('2x+3=11', '4'), ('norm([3,4])', '5'), ('1/2+1/3', '5/6')])
def test_existing_math(client, auth, question, expected):
    response = client.post('/api/v1/math/question', data={'question': question}, headers=auth)
    assert response.status_code == 200, response.text
    result = response.json()
    assert result['route'] == 'solver' and result['status'] == 'solved'
    assert result['solution']['solution'] == expected
    assert result['solution']['verified']


@pytest.mark.parametrize('question', [
    'Ada has 3 apples and buys 4 more. How many apples does she have?',
    'Find the area of a triangle with base 4 cm and height 6 cm.',
    'Explain why 2x + 3 = 11.',
    'ஒரு முக்கோணத்தின் பரப்பளவு என்ன?',
])
def test_prose_never_reaches_equation_solver(client, auth, monkeypatch, question):
    def forbidden(*args):
        raise AssertionError('Prose was sent to the equation solver')
    monkeypatch.setattr('app.main.solve', forbidden)
    response = client.post('/api/v1/math/question', data={'question': question, 'variable': 'x'}, headers=auth)
    result = response.json()
    assert response.status_code == 200
    assert result['route'] == 'interpretation'
    expected = 'review_required' if question.startswith(('Ada has', 'Find the area')) else 'unsupported'
    assert result['status'] == expected
    assert result['question'] == question and result['solution'] is None


@pytest.mark.parametrize('fmt', ['JPEG', 'PNG', 'WEBP'])
@pytest.mark.parametrize('text', ['', '2x+3=11'])
def test_images_and_combined_require_review(client, auth, fmt, text):
    response = client.post('/api/v1/math/question', data={'question': text}, files={'file': image_file(fmt)}, headers=auth)
    assert response.status_code == 200, response.text
    result = response.json()
    assert result['status'] == 'manual_required' and result['route'] == 'image'
    assert result['solution'] is None and result['upload']['steps'] == []
    assert result['question'] == text


def test_transcription_is_review_only_and_failure_is_honest(client, auth, monkeypatch):
    class DraftProvider:
        async def transcribe(self, image, mime):
            return ['2x+3=11']
    monkeypatch.setattr('app.main.get_provider', lambda session: DraftProvider())
    result = client.post('/api/v1/math/question', files={'file': image_file()}, headers=auth).json()
    assert result['status'] == 'review_required' and result['solution'] is None
    assert result['upload']['steps'] == ['2x+3=11']
    # Explicitly reviewed text uses the normal text route, not an image answer.
    result = client.post('/api/v1/math/question', data={'question': '2x+3=11'}, headers=auth).json()
    assert result['solution']['solution'] == '4'
    class FailedProvider:
        async def transcribe(self, image, mime):
            raise RuntimeError('provider unavailable')
    monkeypatch.setattr('app.main.get_provider', lambda session: FailedProvider())
    result = client.post('/api/v1/math/question', files={'file': image_file()}, headers=auth).json()
    assert result['status'] == 'manual_required' and result['solution'] is None


@pytest.mark.parametrize('file,status', [
    (('bad.png', b'not an image', 'image/png'), 422),
    (('bad.pdf', b'%PDF', 'application/pdf'), 422),
    (('bad.svg', b'<svg/>', 'image/svg+xml'), 422),
    (('big.png', b'x' * (5 * 1024 * 1024 + 1), 'image/png'), 413),
])
def test_invalid_files(client, auth, file, status):
    response = client.post('/api/v1/math/question', files={'file': file}, headers=auth)
    assert response.status_code == status


def test_bounds_auth_and_unsupported(client, auth):
    assert client.post('/api/v1/math/question', data={'question': '2+2'}).status_code == 401
    assert client.post('/api/v1/math/question', data={'question': '  '}, headers=auth).status_code == 422
    assert client.post('/api/v1/math/question', data={'question': 'x' * 4001}, headers=auth).status_code == 422
    result = client.post('/api/v1/math/question', data={'question': 'sin(x)=0'}, headers=auth).json()
    assert result['status'] == 'unsupported' and result['solution'] is None
    result = client.post('/api/v1/math/question', data={'question': 'x+y=10', 'variable': 'y'}, headers=auth).json()
    assert result['solution']['variable'] == 'y'


@pytest.mark.parametrize('question,expected,kind', [
    ('ஆரம் 7 உள்ள வட்டத்தின் பரப்பளவு காண்க', 'circle_area(7)', 'Geometry · Circle area'),
    ('ஆரம் ௭ உள்ள வட்டத்தின் சுற்றளவு காண்க', 'circumference(7)', 'Geometry · Circle circumference'),
    ('விட்டம் 14 உள்ள வட்டத்தின் பரப்பளவு காண்க', 'circle_area(7)', 'Geometry · Circle area'),
    ('நீளம் 5 அகலம் 3 உள்ள செவ்வகத்தின் பரப்பளவு காண்க', 'rectangle_area(5,3)', 'Geometry · Rectangle area'),
    ('அடிப்பக்கம் 6 உயரம் 4 உள்ள முக்கோணத்தின் பரப்பளவு காண்க', 'triangle_area(6,4)', 'Geometry · Triangle area'),
    ('கணக்கிடுக: 12*8+6', '12*8+6', 'Arithmetic · Evaluate'),
    ('2x + 3 = 11 ஐ தீர்க்கவும்', '2x+3=11', 'Equation · From sentence'),
    ('Find the area of a circle with diameter 14 cm', 'circle_area(7)', 'Geometry · Circle area'),
    ('Find the hypotenuse of a right triangle with legs 3 and 4', 'hypotenuse(3,4)', 'Geometry · Right-triangle hypotenuse'),
    ('Find the area of a square with side 5 cm', 'rectangle_area(5,5)', 'Geometry · Square area'),
    ('Find the mean of 2, 4, 6 and 8', 'mean([2,4,6,8])', 'Statistics · Mean'),
    ('How many ways to choose 3 from 10?', 'choose(10,3)', 'Counting · Combinations'),
    ('Find the probability of 2 favorable out of 5', 'probability(2,5)', 'Probability'),
    ('Please solve 2x+3=11 for me.', '2x+3=11', 'Equation · From sentence'),
])
def test_sentence_questions_propose_typed_model_then_solve(client, auth, question, expected, kind):
    result = client.post('/api/v1/math/question', data={'question': question}, headers=auth).json()
    assert result['route'] == 'interpretation' and result['status'] == 'review_required'
    assert result['proposed_math'] == expected
    assert result['question_type'] == kind
    assert result['solution'] is None and result['assumptions']
    # The confirmed model travels the normal verified solver route on its own.
    solved = client.post('/api/v1/math/question', data={'question': expected}, headers=auth).json()
    assert solved['status'] == 'solved' and solved['solution']['verified']
    assert solved['question_type'] == solved['solution']['topic']


def test_solver_reports_question_type_and_images_guide_diagrams(client, auth):
    result = client.post('/api/v1/math/question', data={'question': '2x+3=11'}, headers=auth).json()
    assert result['question_type'] == result['solution']['topic']
    result = client.post('/api/v1/math/question', files={'file': image_file()}, headers=auth).json()
    assert result['route'] == 'image' and result['solution'] is None
    assert 'diagram' in result['message'].lower()


def test_question_and_working_require_explicit_question_selection(client, auth):
    # Representative reviewed OCR output: do not silently solve the final answer line.
    lines = ['III. 3n + 4 = Tn', '3n + 4 = 40', '3n = 36', 'n = 12']
    combined = client.post('/api/v1/math/question', data={'question': '\n'.join(lines)}, headers=auth).json()
    assert combined['status'] == 'unsupported' and combined['solution'] is None
    selected = client.post('/api/v1/math/question', data={'question': lines[1]}, headers=auth).json()
    assert selected['status'] == 'solved'
    assert selected['solution']['variable'] == 'n'
    assert selected['solution']['solution'] == '12'
    assert selected['solution']['verified'] is True
