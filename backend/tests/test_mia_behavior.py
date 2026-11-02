"""Behavior evals: scripted multi-turn arcs through the Mia orchestrator (mock mode)."""
import asyncio
from app.agents.tools import execute_tool, TOOL_SCHEMAS
from app.math_parser import MathError
import pytest


def _session(client, auth, language='en', question=''):
    r = client.post('/api/v1/tutor/session', json={'language': language, 'mode': 'classroom', 'question': question}, headers=auth)
    assert r.status_code == 200, r.text
    return r.json()


def _turn(client, auth, sid, message, **kw):
    body = {'session_id': sid, 'message': message}
    body.update(kw)
    r = client.post('/api/v1/tutor/turn', json=body, headers=auth)
    assert r.status_code == 200, r.text
    return r.json()


def test_learning_arc_slow_repeat_method_practice(client, auth):
    s = _session(client, auth)
    t1 = _turn(client, auth, s['id'], 'Teach me', equation='2x+3=11')
    assert t1['verified_math']['verified'] is True
    assert t1['whiteboard']
    for item in t1['whiteboard']:
        assert 'equation' in item and 'explanation' not in item
    t2 = _turn(client, auth, s['id'], 'Explain slowly', slow=True)
    assert t2['intent'] == 'explain_slow' and t2['voice_rate'] == 0.65
    t3 = _turn(client, auth, s['id'], 'Repeat this step')
    assert t3['intent'] == 'repeat'
    t4 = _turn(client, auth, s['id'], 'Show another method', method='alternative')
    assert t4['intent'] == 'change_method'
    t5 = _turn(client, auth, s['id'], 'Give me practice')
    assert t5['intent'] == 'practice' and t5['practice'] and 'equation' in t5['practice']
    assert all(t.get('trace') for t in (t1, t2, t3, t4, t5))
    kinds = [e['kind'] for e in t1['trace']]
    assert kinds[0] == 'plan' and kinds[-1] == 'reply'
    h = client.get(f"/api/v1/tutor/session/{s['id']}/history", headers=auth).json()
    assert len(h['turns']) == 10


def test_tamil_pizza_example_uses_context(client, auth):
    s = _session(client, auth, language='ta')
    t = _turn(client, auth, s['id'], 'Show a real-world example', equation='1/2', language='ta', context='pizza')
    assert t['language'] == 'ta' and t['real_world']
    assert t['verified_math']['verified'] is True


def test_tool_loop_falls_back_when_endpoint_refuses(client, auth, monkeypatch):
    from app.providers import ToolsUnsupported

    class RefusingProvider:
        name = 'refusing tools'
        supports_tools = True

        async def explain(self, message, verified):
            return 'Fallback explanation. ' + verified['steps'][1]['explanation']

        async def request_with_tools(self, messages, tools):
            raise ToolsUnsupported('no tools here')

    monkeypatch.setattr('app.main.get_provider', lambda *_: RefusingProvider())
    s = _session(client, auth)
    t = _turn(client, auth, s['id'], 'Teach me', equation='2x+3=11')
    assert t['intent'] == 'teach'
    assert t['reply'] and t['verified_math']['verified'] is True


def test_tool_loop_success_with_stubbed_calls(client, auth, monkeypatch):
    class ToolProvider:
        name = 'stub tools'
        supports_tools = True
        calls = 0

        async def explain(self, message, verified):
            return 'Stubbed.'

        async def request_with_tools(self, messages, tools):
            ToolProvider.calls += 1
            if ToolProvider.calls == 1:
                return {'tool_calls': [{'id': 'c1', 'name': 'solve_equation', 'arguments': {'equation': '2x+3=11'}}]}
            return {'content': 'Two x plus three equals eleven, so x is four.'}

    ToolProvider.calls = 0
    monkeypatch.setattr('app.main.get_provider', lambda *_: ToolProvider())
    s = _session(client, auth)
    t = _turn(client, auth, s['id'], 'Teach me', equation='2x+3=11')
    assert t['intent'].startswith('agentic')
    kinds = [e['kind'] for e in t['trace']]
    assert 'tool' in kinds and 'observation' in kinds
    assert t['verified_math']['verified'] is True and t['whiteboard']


def test_tool_schemas_and_dispatcher():
    names = [t['function']['name'] for t in TOOL_SCHEMAS]
    assert names == ['solve_equation', 'verify_steps', 'get_practice']
    solved = asyncio.run(execute_tool('solve_equation', {'equation': '2x+3=11'}))
    assert solved['verified'] is True and solved['solution'] == '4'
    feedback = asyncio.run(execute_tool('verify_steps', {'steps': ['2x+3=11', '2x=8', 'x=4']}))
    assert feedback['valid'] is True
    practice = asyncio.run(execute_tool('get_practice', {'category': 'addition'}))
    assert practice['available'] is True and 'equation' in practice
    with pytest.raises(MathError):
        asyncio.run(execute_tool('nope', {}))
