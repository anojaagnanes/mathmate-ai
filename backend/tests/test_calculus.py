import pytest
from app.maths import solve, analyze, MathError

@pytest.mark.parametrize('source,expected', [
    ('diff(x^3, x)','3*x**2'), ('d/dx (x³)','3*x**2'),
    ('diff(3y^2-2y+7, y)','6*y - 2'), ('diff(5, n)','0'),
    ('diff(0, x)','0'), ('diff(x^6, x)','6*x**5'),
    ('diff(x/2, x)','1/2'), ('integrate(x^2, x)','x**3/3 + C'),
    ('integrate(2y+3, y)','y**2 + 3*y + C'), ('integrate(0, x)','0 + C'),
    ('integrate(5, n)','5*n + C'), ('integrate(x^6, x)','x**7/7 + C'),
])
def test_polynomial_calculus(source,expected):
    r=solve(source)
    assert r['kind']=='calculus' and r['solution']==expected and r['verified']
    assert all(s['latex'] for s in r['steps'])
    assert 'Check:' in r['steps'][-1]['explanation']

@pytest.mark.parametrize('source', [
    'diff(x^3)', 'diff(x^3,x,2)', 'diff(x^3, __import__("os"))',
    'diff(x^3, x).__class__', 'diff(sin(x),x)', 'integrate(1/x,x)',
    'integrate(x,x,0,1)', 'diff(x+y,x)', 'diff(sqrt(x)^2,x)',
    'diff(exp(1000),x)', 'diff(x^7,x)', 'diff(x^3,foo)',
    'diff((x+1,x)', 'diff(x),x)', 'integrate(diff(x,x),x)', 'dy/dx',
])
def test_unsupported_calculus_is_safe(source):
    with pytest.raises(MathError): solve(source)


def test_calculus_variable_and_step_boundaries():
    assert solve('diff(y^2,y)','y')['solution']=='2*y'
    with pytest.raises(MathError): solve('diff(y^2,y)','x')
    with pytest.raises(MathError): analyze(['diff(x^3,x)'])


def test_calculus_api_and_mia(client,auth):
    r=client.post('/api/v1/math/solve',json={'equation':'integrate(x^2,x)'},headers=auth)
    assert r.status_code==200,r.text
    assert r.json()['solution']=='x**3/3 + C'
    r=client.post('/api/v1/tutor/chat',json={'equation':'diff(x^3,x)','message':'Explain the rule'},headers=auth)
    assert r.status_code==200,r.text
    assert r.json()['verified_math']['solution']=='3*x**2'
    assert 'Power rule' in r.json()['message']
