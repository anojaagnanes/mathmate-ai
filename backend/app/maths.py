"""Bounded recursive-descent parser. Student text never reaches eval or sympify."""
import re
import sympy as sp

x = sp.Symbol('x', real=True)


class MathError(ValueError):
    pass


def expression(source: str):
    if not source or len(source) > 200:
        raise MathError('Use an expression of 1–200 characters.')
    source = source.replace('−', '-').replace('×', '*').replace('÷', '/')
    if re.search(r'[^0-9x+*/().\-\s]', source):
        raise MathError('Use numbers, x, parentheses and + - * / only.')
    tokens = re.findall(r'\d+(?:\.\d+)?|[x+*/().-]', source)
    if len(tokens) > 100:
        raise MathError('This expression is too long.')
    # Insert conventional implicit multiplication (2x, 2(x+1), (x+1)2).
    expanded = []
    for t in tokens:
        if expanded and expanded[-1][0].isdigit() and t[0].isdigit():
            raise MathError('Put an operator between numbers; for example, 1 + 2.')
        if expanded and (expanded[-1] == 'x' or expanded[-1] == ')' or expanded[-1][0].isdigit()) and (t == 'x' or t == '(' or t[0].isdigit()):
            expanded.append('*')
        expanded.append(t)
    tokens = expanded
    i = 0

    def atom(depth=0):
        nonlocal i
        if depth > 15 or i >= len(tokens):
            raise MathError('Incomplete expression or too many nested parentheses.')
        t = tokens[i]
        i += 1
        if t in ('+', '-'):
            return (1 if t == '+' else -1) * atom(depth + 1)
        if t == '(':
            result = add(depth + 1)
            if i >= len(tokens) or tokens[i] != ')':
                raise MathError('Close each parenthesis.')
            i += 1
            return result
        if t == 'x':
            return x
        if re.fullmatch(r'\d+(?:\.\d+)?', t) and len(t) <= 12:
            return sp.Rational(t)
        raise MathError('Unsupported number or expression.')

    def multiply(depth):
        nonlocal i
        result = atom(depth)
        while i < len(tokens) and tokens[i] in ('*', '/'):
            op = tokens[i]
            i += 1
            right = atom(depth)
            if op == '/':
                if right == 0:
                    raise MathError('Division by zero is not defined.')
                if right.has(x):
                    raise MathError('Division by a variable expression is outside this lesson.')
                result /= right
            else:
                result *= right
            if sp.Poly(result, x).degree() > 1:
                raise MathError('Only linear expressions are supported.')
        return result

    def add(depth):
        nonlocal i
        result = multiply(depth)
        while i < len(tokens) and tokens[i] in ('+', '-'):
            op = tokens[i]
            i += 1
            right = multiply(depth)
            result = result + right if op == '+' else result - right
        return result

    result = sp.expand(add(0))
    if i != len(tokens):
        raise MathError('Unexpected symbol. Check your expression.')
    if sp.Poly(result, x).degree() > 1:
        raise MathError('Only linear expressions are supported.')
    return result


def sides(equation):
    if equation.count('=') != 1:
        raise MathError('Enter one equation with one equals sign.')
    return tuple(expression(s) for s in equation.split('='))


def solve(equation: str):
    left, right = sides(equation)
    difference = sp.expand(left - right)
    a, b = difference.coeff(x), difference.subs(x, 0)
    steps = [{'equation': equation, 'explanation': 'Start with the original equation.'}]
    if a == 0:
        kind = 'infinite' if b == 0 else 'none'
        steps.append({'equation': f'{b} = 0', 'explanation': 'Both sides are identical, so every real x works.' if b == 0 else 'This is a contradiction, so no value of x works.'})
        return dict(kind=kind, solution=None, steps=steps, verified=True, latex=sp.latex(left) + '=' + sp.latex(right))
    answer = -b / a
    left_constant = left.subs(x, 0)
    right_constant = right.subs(x, 0)
    if right.coeff(x):
        steps.append({'equation': f'{a}*x + ({left_constant}) = {right_constant}', 'explanation': f'Subtract {right.coeff(x)} times x from both sides and collect the x terms.'})
    steps.extend([
        {'equation': f'({a}*x + ({left_constant})) - ({left_constant}) = ({right_constant}) - ({left_constant})', 'explanation': f'Subtract {left_constant} from both sides. Doing the same thing to each side keeps the equation balanced.'},
        {'equation': f'{a}*x = {-b}', 'explanation': 'Simplify both sides. The constant on the left cancels out.'},
        {'equation': f'({a}*x)/({a}) = ({-b})/({a})', 'explanation': f'Divide both sides by {a}, the nonzero coefficient of x.'},
        {'equation': f'x = {answer}', 'explanation': 'Simplify the division. You have isolated x!'},
        {'equation': f'{left.subs(x, answer)} = {right.subs(x, answer)}', 'explanation': f'Substitute x = {answer} into the original equation. Both sides agree.'},
    ])
    return dict(kind='unique', solution=str(answer), steps=steps, verified=True, latex=sp.latex(left) + '=' + sp.latex(right))


def analyze(steps: list[str]):
    original = solve(steps[0])
    for index, step in enumerate(steps[1:], 1):
        try:
            current = solve(step)
            equivalent = current['kind'] == original['kind'] and current['solution'] == original['solution']
            message = 'This step changes the solution set. Apply the same reversible operation to both sides.'
            error_code = 'changed_solution'
            if not equivalent:
                prev_left, prev_right = sides(steps[index - 1])
                next_left, next_right = sides(step)
                if (prev_left == next_left) != (prev_right == next_right):
                    message = 'Only one side changed. Keep the equation balanced by applying the same operation to both sides.'
                    error_code = 'one_side_changed'
        except MathError as exc:
            equivalent, message = False, str(exc)
            error_code = 'division_by_zero' if 'zero' in message else 'unsupported_input'
        if not equivalent:
            return dict(valid=False, first_incorrect_step=index + 1, message=message, error_code=error_code, corrected=original)
    return dict(valid=True, first_incorrect_step=None, message='Every equation has the same solution set. Nicely done!', error_code=None, corrected=original)
