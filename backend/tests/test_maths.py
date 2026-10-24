import pytest
from app.maths import expression, solve, analyze, MathError


@pytest.mark.parametrize('equation,kind,value', [('2x+3=11','unique','4'),('3x+2=x+10','unique','4'),('2(x+1)=8','unique','3'),('x/2=3','unique','6'),('0.5x=1','unique','2'),('2x=2x','infinite',None),('2x+1=2x','none',None),('0x=0','infinite',None),('-3x=2','unique','-2/3')])
def test_solutions(equation, kind, value):
    result = solve(equation)
    assert (result['kind'], result['solution']) == (kind, value)


@pytest.mark.parametrize('source', ['__import__("os")', '1/0', 'x/(x-1)', 'x;', '1..2', '1 2', '1.2 3.4', '1e100', '('*30+'x'+')'*30, '123456789012345', 'x +', ''])
def test_restricted_parser(source):
    with pytest.raises(MathError):
        expression(source)


def test_valid_transformations():
    assert analyze(['2x+3=11', '2x=8', 'x=4'])['valid']
    assert analyze(['x=x', '0=0'])['valid']


def test_first_incorrect_step():
    result = analyze(['2x+3=11', '2x=8', 'x=5', 'x=4'])
    assert result['first_incorrect_step'] == 3
    assert not result['valid']


def test_division_zero_transformation():
    assert analyze(['2x=8','x=8/0'])['first_incorrect_step'] == 2


def test_solution_set_change():
    assert not analyze(['x=4', '0=0'])['valid']
    assert not analyze(['x=x', 'x=4'])['valid']


def test_generated_steps_equivalent_before_substitution():
    result = solve('3x+2=x+10')
    assert analyze([s['equation'] for s in result['steps'][:-1]])['valid']


@pytest.mark.parametrize('equation', ['2x+3=11', '3x+2=x+10', '-2x-3=9', 'x/2+1=3', '3=2x+1'])
def test_teaching_steps_are_equivalent(equation):
    result = solve(equation)
    assert analyze([s['equation'] for s in result['steps'][:-1]])['valid']
    assert 'Substitute' in result['steps'][-1]['explanation']


def test_one_side_error_is_specific():
    result = analyze(['2x+3=11', '2x=11'])
    assert result['error_code'] == 'one_side_changed'
