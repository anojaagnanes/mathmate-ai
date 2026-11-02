import pytest
import sympy as sp
from app.maths import solve, expression, analyze, MathError
from app.math_runtime import calculate

@pytest.mark.parametrize('text,answer', [('3x+4=10','2'),('3y+5=20','5'),('3n+4=40','12'),('4z-8=12','5'),('2theta=6','3'),('2alpha=6','3'),('2beta=6','3'),('x²+2x+1=0','-1')])
def test_variable_equations(text, answer):
    result = solve(text)
    assert result['solution'] == answer
    assert result['verified'] and result['kind'] == 'unique'
    assert 'Substitute' in result['steps'][-1]['explanation']

@pytest.mark.parametrize('text,roots', [('x^2-5x+6=0', ['2','3']),('x²-9=0',['-3','3']),('x*x=2',['-sqrt(2)','sqrt(2)']),('x**2=0',['0'])])
def test_quadratic(text, roots):
    result = solve(text)
    assert result['solutions'] == roots
    assert result['verified']
    assert all(s.get('latex') for s in result['steps'])

@pytest.mark.parametrize('text,result', [('sqrt(25)','5'),('√25','5'),('2^5','32'),('1/2+1/3','5/6'),('2^-2','1/4'),('-2^2','-4'),('(-2)^2','4'),('1e3+2','1002'),('sqrt(2)*sqrt(2)','2'),('(x+1)^3','x**3 + 3*x**2 + 3*x + 1')])
def test_expressions(text, result):
    output = solve(text)
    assert output['kind'] == 'expression'
    assert output['solution'] == result and output['verified']


def test_parameter_and_ambiguity():
    result = solve('x+y=10')
    assert result['kind'] == 'underdetermined' and not result['verified']
    assert result['solution'] is None
    result = solve('x+y=10', 'y')
    assert result['kind'] == 'parametric' and result['solution'] == '10 - x' and result['verified']
    with pytest.raises(MathError): solve('x*y=10','x')
    with pytest.raises(MathError): solve('0*x+y=1','x')
    with pytest.raises(MathError): solve('x+y=10','z')


def test_domains_and_identities():
    assert solve('x^2=-1')['kind'] == 'none'
    assert solve('y=y')['kind'] == 'infinite'
    assert solve('y+1=y')['kind'] == 'none'
    assert solve('1=1')['kind'] == 'infinite'
    with pytest.raises(MathError): solve('1/x=0')
    with pytest.raises(MathError): solve('sqrt(-1)')


def test_step_sets_and_variable_changes():
    assert analyze(['3y+5=20','3y=15','y=5'])['valid']
    assert analyze(['x^2-9=0','x^2=9'])['valid']
    assert not analyze(['x^2=9','x=3'])['valid']
    assert not analyze(['y=5','x=5'])['valid']
    assert analyze(['3n+4=40','3n=36','n=11'])['first_incorrect_step'] == 3

@pytest.mark.parametrize('text', ['x^3=1'])
def test_later_phase_errors(text):
    with pytest.raises(MathError): solve(text)

@pytest.mark.parametrize('text', ['__import__("os")','x.__class__','open(1)','lambda x: x','[x for x in y]','x;1','1..2','1 2','x+','2^999','2^2^2','(2^6)^6^6','1e999','('*20+'x'+')'*20,'x'*201,'0^-1','0^0','1/0','sqrt(x)^2=x','x^0=1'])
def test_reject_unsafe_or_expensive(text):
    with pytest.raises(MathError): solve(text)


def test_worker_success_and_deadline():
    assert calculate('solve', '3y+5=20')['solution'] == '5'
    with pytest.raises(MathError, match='timed out'):
        calculate('solve', '(x+1)^6', timeout=0)
    assert calculate('solve', '2^5')['solution'] == '32'


def test_api_expanded_contract_and_teacher(client, auth):
    for text,kind in [('3y+5=20','unique'),('x^2-9=0','multiple'),('sqrt(25)','expression'),('x+y=10','underdetermined')]:
        response = client.post('/api/v1/math/solve', json={'equation':text}, headers=auth)
        assert response.status_code == 200, response.text
        assert response.json()['kind'] == kind
    result = client.post('/api/v1/math/solve', json={'equation':'x+y=10','variable':'x'}, headers=auth).json()
    assert result['solution'] == '10 - y'
    result = client.post('/api/v1/tutor/chat', json={'equation':'sqrt(25)','message':'Why?'}, headers=auth)
    assert result.status_code == 200 and result.json()['verified_math']['solution'] == '5'
    assert 'balanced scale' not in result.json()['message']
    result = client.post('/api/v1/math/validate', json={'steps':['3n+4=40','n=12']}, headers=auth)
    assert result.status_code == 200 and result.json()['valid']


def test_worker_capacity_is_bounded(monkeypatch):
    from app import math_runtime
    from threading import BoundedSemaphore
    monkeypatch.setattr(math_runtime, 'SLOTS', BoundedSemaphore(0))
    with pytest.raises(MathError, match='busy'):
        math_runtime.calculate('solve', 'x=1')


def test_worker_startup_has_its_own_deadline(monkeypatch):
    from app import math_runtime
    monkeypatch.setattr(math_runtime, 'STARTUP_TIMEOUT_SECONDS', 0)
    with pytest.raises(MathError, match='could not start'):
        math_runtime.calculate('solve', '2+2')
