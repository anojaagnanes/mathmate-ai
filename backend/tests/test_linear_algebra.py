import pytest
from app.maths import solve, analyze, MathError

@pytest.mark.parametrize('source,answer', [
    ('Matrix([[1,2],[3,4]])','Matrix([[1, 2], [3, 4]])'),
    ('det([[1,2],[3,4]])','-2'), ('det(Matrix([[7]]))','7'),
    ('det([[1,2,3],[0,1,4],[5,6,0]])','1'),
    ('inverse([[1,2],[3,4]])','Matrix([[-2, 1], [3/2, -1/2]])'),
    ('inverse([[2]])','Matrix([[1/2]])'),
    ('transpose([[1,2,3],[4,5,6]])','Matrix([[1, 4], [2, 5], [3, 6]])'),
    ('matrixadd([[1,2]],[[3,4]])','Matrix([[4, 6]])'),
    ('matmul([[1,2],[3,4]],[[5],[6]])','Matrix([[17], [39]])'),
    ('Vector([1/2,0.5])','Matrix([[1/2], [1/2]])'),
    ('dot([1,2],[3,4])','11'), ('dot([1,2,3],[4,5,6])','32'),
    ('cross([1,0,0],[0,1,0])','Matrix([[0], [0], [1]])'),
    ('cross([0,1,0],[1,0,0])','Matrix([[0], [0], [-1]])'),
    ('norm([3,4])','5'), ('norm([1,1])','sqrt(2)'), ('norm([0,0])','0')])
def test_exact_results(source,answer):
    r=solve(source)
    assert r['kind']=='linear_algebra' and r['solution']==answer and r['verified']
    assert all(step['latex'] for step in r['steps'])

@pytest.mark.parametrize('source', [
    'inverse([[1,2],[2,4]])', 'det([[1,2]])', 'Matrix([[1],[2,3]])',
    'Matrix([])', 'Matrix([[]])', 'Matrix([[1,2,3,4]])',
    'Matrix([[1],[2],[3],[4]])', 'Matrix([[x]])', 'Matrix([[sqrt(2)]])',
    'matmul([[1,2]],[[1,2]])', 'matrixadd([[1]],[[1,2]])',
    'dot([1,2],[1,2,3])','cross([1,2],[3,4])','Vector([1])',
    'norm([1,2,3,4])','det([[1/0]])','det([[2^999]])',
    'Matrix([[__import__("os")]])', 'Matrix([[1]]).__class__',
    'Matrix([[1],[2]])+Matrix([[1],[2]])', 'dot([1,2],[3,4],5)',
    'det([[1,2],(3,4]])', 'det([[1,]])', 'norm([1,,2])'])
def test_safe_dimension_domain_and_syntax_errors(source):
    with pytest.raises(MathError): solve(source)


def test_selector_and_validation_boundaries():
    with pytest.raises(MathError): solve('norm([3,4])','x')
    with pytest.raises(MathError): analyze(['Matrix([[1]])'])


def test_api_and_teacher(client,auth):
    r=client.post('/api/v1/math/solve',json={'equation':'inverse([[1,2],[3,4]])'},headers=auth)
    assert r.status_code==200,r.text
    assert r.json()['kind']=='linear_algebra'
    r=client.post('/api/v1/tutor/chat',json={'equation':'dot([1,2],[3,4])','message':'How?'},headers=auth)
    assert r.status_code==200,r.text
    assert r.json()['verified_math']['solution']=='11'
    assert 'corresponding components' in r.json()['message']
