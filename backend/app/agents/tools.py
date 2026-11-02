"""Mia tool bindings. Deterministic math first, Meta only for prose."""
import base64
from starlette.concurrency import run_in_threadpool
from ..math_parser import MathError
from ..math_runtime import calculate
from ..question_input import needs_interpretation, interpret_question
from ..document_text import extract_pdf, DocumentError, MAX_BYTES
from .practice import PracticeAgent


async def tool_solve(equation, variable=None):
    return await run_in_threadpool(calculate, 'solve', equation, variable)


async def tool_verify_steps(steps):
    return await run_in_threadpool(calculate, 'analyze', steps)


async def tool_review_work(steps):
    return await run_in_threadpool(calculate, 'review_work', steps)


async def tool_transcribe(provider, image_b64, mime):
    try:
        raw = base64.b64decode(image_b64, validate=True)
    except Exception:
        raise MathError('Image data could not be decoded.')
    if len(raw) > 5 * 1024 * 1024:
        raise MathError('Choose an image smaller than 5 MB.')
    from .vision import VisionAgent
    return await VisionAgent(provider).extract(raw, mime or 'image/png')


async def tool_extract_pdf(pdf_b64):
    try:
        raw = base64.b64decode(pdf_b64, validate=True)
    except Exception:
        raise DocumentError('PDF data could not be decoded.')
    if len(raw) > MAX_BYTES:
        raise DocumentError('Choose a PDF no larger than 5 MB.')
    return await run_in_threadpool(extract_pdf, raw)


def tool_classify_intent(message, equation=''):
    text = (message or '').lower()
    if any(k in text for k in ['tamil', 'tamilil', 'tamilில்', 'தமிழ்']):
        if any(k in text for k in ['speak', 'explain', 'switch', 'reply', 'பேசு', 'சொல்']):
            return 'switch_language'
    if any(k in text for k in ['slow', 'slowly', 'slower', 'மெதுவா', 'மெதுவாக']):
        return 'explain_slow'
    if any(k in text for k in ['repeat', 'again', 'replay', 'மீண்டும்', 'திரும்ப']):
        return 'repeat'
    if any(k in text for k in ['another method', 'different method', 'other way', 'change method', 'வேறு முறை']):
        return 'change_method'
    if any(k in text for k in ['example', 'real world', 'real-world', 'உதாரணம்']):
        return 'real_world'
    if any(k in text for k in ['practice', 'quiz', 'exercise', 'drill', 'பயிற்சி']):
        return 'practice'
    if any(k in text for k in ['why', 'how', 'what do you mean', 'what does', 'confus', 'understand', 'dont understand', 'do not understand',
                             'lost', 'stuck', 'help', 'unclear', 'not clear', 'dont get', 'do not get', 'explain', 'meaning',
                             'ஏன்', 'எப்படி', 'புரியவில்லை', 'புரியல', 'குழப்பம்', 'தெரியவில்லை', 'தெரியல', 'உதவி', 'விளக்கு']):
        return 'followup'
    if equation and len(equation.strip()) > 0:
        return 'solve'
    if '?' in message or len(message.split()) > 12:
        return 'followup'
    return 'solve'


def tool_detect_language(message, explicit=None):
    if explicit in ('en', 'ta'):
        return explicit
    if any('\u0b80' <= ch <= '\u0bff' for ch in message):
        return 'ta'
    return 'en'


async def tool_practice_next(provider, topic='fractions', category='addition', history=(), seen=()):
    agent = PracticeAgent()
    if topic == 'fractions':
        return await agent.generate_with_provider(provider, category, history, seen)
    return agent.generate(category, history, seen)


TOOL_SCHEMAS = [
    {'type': 'function', 'function': {
        'name': 'solve_equation',
        'description': 'Solve a maths equation or expression with the verified SymPy solver. Use for any new question.',
        'parameters': {'type': 'object', 'properties': {
            'equation': {'type': 'string', 'description': 'The equation or expression, max 200 chars'},
            'variable': {'type': 'string', 'description': 'Optional target variable'}},
            'required': ['equation'], 'additionalProperties': False}}},
    {'type': 'function', 'function': {
        'name': 'verify_steps',
        'description': 'Check student working lines and find the first incorrect step.',
        'parameters': {'type': 'object', 'properties': {
            'steps': {'type': 'array', 'items': {'type': 'string'}, 'description': '1-30 solution lines'}},
            'required': ['steps'], 'additionalProperties': False}}},
    {'type': 'function', 'function': {
        'name': 'get_practice',
        'description': 'Generate one verified adaptive practice question.',
        'parameters': {'type': 'object', 'properties': {
            'category': {'type': 'string', 'description': 'addition, comparison or equivalence'}},
            'required': [], 'additionalProperties': False}}},
]


async def execute_tool(name, args):
    from ..math_parser import MathError
    if name == 'solve_equation':
        equation = str((args or {}).get('equation', ''))[:200]
        variable = (args or {}).get('variable') or None
        if not equation.strip():
            raise MathError('No equation supplied.')
        solved = await tool_solve(equation, variable if isinstance(variable, str) and len(variable) <= 5 else None)
        return {'verified': solved.get('verified'), 'topic': solved.get('topic'), 'solution': solved.get('solution'),
                'steps': [{'equation': s.get('equation'), 'explanation': s.get('explanation')} for s in solved.get('steps', [])[:12]]}
    if name == 'verify_steps':
        steps = list((args or {}).get('steps') or [])[:30]
        if not steps:
            raise MathError('No steps supplied.')
        feedback = await tool_verify_steps([str(s)[:200] for s in steps])
        return {'valid': feedback.get('valid'), 'first_incorrect_step': feedback.get('first_incorrect_step'), 'message': feedback.get('message')}
    if name == 'get_practice':
        from .practice import PracticeAgent
        category = str((args or {}).get('category') or 'addition')[:20]
        if category not in ('addition', 'comparison', 'equivalence'):
            category = 'addition'
        question = PracticeAgent().generate(category)
        if not question:
            return {'available': False}
        return {'available': True, 'equation': question['equation'], 'hint': question['hint'], 'difficulty': question['difficulty']}
    raise MathError(f'Unknown tool: {name}')


def tool_needs_interpretation(text):
    return needs_interpretation(text)


def tool_interpret(text):
    return interpret_question(text)
