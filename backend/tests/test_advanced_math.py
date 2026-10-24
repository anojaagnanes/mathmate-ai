import pytest
import sympy as sp
from app.maths import solve, analyze, function_graph, MathError

@pytest.mark.parametrize('source,expected', [('sin(pi/2)','1'),('cos(pi)','-1'),('tan(pi/4)','1'),('log(E)','1'),('exp(0)','1'),('sin(π/2)','1'),('log(1)','0'),('sin(x)^2+cos(x)^2','sin(x)**2 + cos(x)**2')])
def test_functions(source,expected):
    assert solve(source)['solution']==expected
    assert solve(source)['verified']


def test_domains_survive_cancellation():
    assert solve('log(x)-log(x)')['domain_conditions']==['x > 0', 'x > 0']
    assert solve('sqrt(x)^2')['domain_conditions']==['x >= 0']
    for source in ['log(0)','log(-1)','tan(pi/2)','log(x)=log(x)','sqrt(x)^2=x','exp(1000)','exp(exp(50))','sin.__class__','sin(x,y)','sin x']:
        with pytest.raises(MathError): solve(source)

@pytest.mark.parametrize('source,assignments', [('2x+y=7; x-y=2',{'x':'3','y':'1'}),('x+y=3 with x-y=1',{'x':'2','y':'1'}),('x+y+z=6; x-y=0; z=2',{'x':'2','y':'2','z':'2'}),('y=1; x+y=3',{'x':'2','y':'1'})])
def test_systems(source,assignments):
    result=solve(source)
    assert result['kind']=='system' and result['assignments']==assignments and result['verified']
    assert any('Substitute' in s['explanation'] for s in result['steps'])
    assert all(s['latex'] for s in result['steps'])


def test_system_special_cases():
    assert solve('x+y=2; 2x+2y=4')['kind']=='parametric'
    assert solve('x+y=2; x+y=3')['kind']=='none'
    for s in ['x*y=2; x+y=3', 'x=1;', 'x=1;x=2;x=3;x=4']:
        with pytest.raises(MathError): solve(s)
    with pytest.raises(MathError): analyze(['x+y=2;x-y=0'])

@pytest.mark.parametrize('source,expected', [('2x+3>7','Interval.open(2, oo)'),('-2x+3>7','Interval.open(-oo, -2)'),('x²-9<=0','Interval(-3, 3)'),('x²<0','No real solutions'),('x²>=0','All real numbers'),('3<4','All real numbers'),('3>4','No real solutions'),('2y≤4','Interval(-oo, 2)')])
def test_inequalities(source,expected):
    result=solve(source)
    assert result['kind']=='inequality' and result['solution']==expected and result['verified']
    if source.startswith('-2'):
        assert any('Reverse' in s['explanation'] for s in result['steps'])


def test_inequality_boundaries():
    for source in ['0<x<2','x+y>2','sin(x)>0','x^3>1']:
        with pytest.raises(MathError): solve(source)
    with pytest.raises(MathError): analyze(['x>1','x>2'])

@pytest.mark.parametrize('source', ['x^2','y = x^2','sin(x)','cos(x)','exp(x)','sqrt(x)','log(x)','tan(x)','log(x)-log(x)'])
def test_graph_domain_and_finite_samples(source):
    result=function_graph(source)
    points=[p for segment in result['segments'] for p in segment]
    assert 0<len(points)<=401
    if source.startswith('log'): assert all(p['x']>0 for p in points)
    if source=='sqrt(x)': assert all(p['x']>=0 for p in points)
    if source=='tan(x)':
        assert len(result['segments'])==5
        for segment in result['segments']:
            assert not any(segment[0]['x'] < pole < segment[-1]['x'] for pole in [-3*float(sp.pi)/2,-float(sp.pi)/2,float(sp.pi)/2,3*float(sp.pi)/2])


def test_graph_restrictions():
    for s in ['tan(100*x)','y+x','sin(x^2)','1/x','tan(100*x)-tan(100*x)']:
        with pytest.raises(MathError): function_graph(s)
    with pytest.raises(MathError): function_graph('x',5,-5)


def test_advanced_api(client,auth):
    for source in ['2x+y=7; x-y=2','-2x+3>7','sin(pi/2)','log(x)']:
        r=client.post('/api/v1/math/solve',json={'equation':source},headers=auth)
        assert r.status_code==200, r.text
    r=client.post('/api/v1/math/function-graph',json={'expression':'x^2'},headers=auth)
    assert r.status_code==200,r.text
    assert len(r.json()['segments'][0])==401
    assert client.post('/api/v1/math/function-graph',json={'expression':'x','minimum':8,'maximum':2},headers=auth).status_code==422
    r=client.post('/api/v1/tutor/chat',json={'equation':'2x+y=7; x-y=2','message':'Explain'},headers=auth)
    assert r.status_code==200 and r.json()['verified_math']['assignments']=={'x':'3','y':'1'}
