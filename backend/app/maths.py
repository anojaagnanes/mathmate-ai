"""Phase 1 deterministic maths handlers, shared by typed and confirmed image input."""
import sympy as sp
from .math_parser import MathError, VARIABLES, parse

x = sp.Symbol('x', real=True)  # Compatibility for existing callers.


def expression(source):
    return parse(source)[0]


def sides(equation):
    if equation.count('=') != 1:
        raise MathError('Enter one equation with one equals sign. Systems and inequalities are later phases.')
    return tuple(expression(part) for part in equation.split('='))


def step(value, explanation, latex=None):
    return {'equation': str(value), 'explanation': explanation, 'latex': latex}


def equation_step(left, right, explanation):
    return step(f'{left} = {right}', explanation, sp.latex(left) + '=' + sp.latex(right))


def solve(equation, variable=None):
    if not equation or len(equation) > 200:
        raise MathError('Use a question of 1–200 characters.')
    if variable and variable not in VARIABLES:
        raise MathError('Choose a supported variable such as x, y, z or n.')
    if '=' not in equation:
        value, names = parse(equation)
        result = sp.expand(value)
        topic = 'Algebraic expression' if names else 'Arithmetic'
        return dict(kind='expression', solution=str(result), solutions=[], variable=None,
                    variables=sorted(names), topic=topic, domain='real', verified=True,
                    latex=sp.latex(result), steps=[step(equation, 'Read the expression.'),
                    step(str(result), 'Evaluate exact arithmetic and collect like terms. An expression without an equals sign is simplified, not solved for a variable.', sp.latex(result))])
    if equation.count('=') != 1:
        raise MathError('Enter a single equation. Simultaneous equations are planned for Phase 2.')
    left, left_names = parse(equation.split('=')[0])
    right, right_names = parse(equation.split('=')[1])
    names = sorted(left_names | right_names)
    if variable and names and variable not in names:
        raise MathError('The selected variable does not occur in this question.')
    target = variable or (names[0] if len(names) == 1 else None)
    steps = [equation_step(left, right, 'Start with the original equation.')]
    base = dict(solution=None, solutions=[], variable=target, variables=names, domain='real',
                steps=steps, verified=True, latex=sp.latex(left)+'='+sp.latex(right))
    difference = sp.expand(left-right)
    if difference == 0 or not difference.free_symbols:
        kind = 'infinite' if difference == 0 else 'none'
        steps.append(equation_step(difference, sp.Integer(0), 'Both sides are identical; every real value is allowed.' if kind == 'infinite' else 'This is a contradiction. There are no real solutions.'))
        return dict(base, kind=kind, topic='Identity' if kind == 'infinite' else 'Contradiction')
    if len(names) > 1 and not target:
        steps.append(step(equation, 'One equation with multiple variables does not determine unique numerical values. Choose the variable to express in terms of the others.'))
        return dict(base, kind='underdetermined', topic='Multivariable equation', verified=False)
    symbol = sp.Symbol(target, real=True)
    if not difference.is_polynomial(symbol):
        raise MathError('Solving roots of variable expressions is not supported yet. Phase 1 solves linear and quadratic polynomial equations.')
    polynomial = sp.Poly(difference, symbol)
    degree = polynomial.degree()
    if degree == 0:
        raise MathError('The selected variable cancels out; the remaining variables require additional conditions.')
    if degree > 2:
        raise MathError('Phase 1 simplifies polynomial expressions up to degree 6, but solves equations only up to degree 2.')
    if len(names) > 1 and degree != 1:
        raise MathError('Multivariable quadratic equations require parameter/domain cases not supported in Phase 1.')
    if degree == 1:
        a = polynomial.nth(1)
        if a.free_symbols or a.is_zero is not False:
            raise MathError('A variable coefficient requires additional conditions. Use a nonzero numeric coefficient for the selected variable.')
        b = polynomial.nth(0)
        answer = sp.simplify(-b/a)
        left_constant = left.subs(symbol, 0)
        right_constant = right.subs(symbol, 0)
        if sp.expand(right).coeff(symbol):
            steps.append(equation_step(a*symbol+left_constant, right_constant, f'Subtract {sp.expand(right).coeff(symbol)} times {target} from both sides and collect the {target} terms.'))
        steps.append(equation_step(a*symbol, -b, f'Subtract {left_constant} from both sides, then collect like terms.'))
        steps.append(step(f'({a}*{target})/({a}) = ({-b})/({a})', f'Divide both sides by {a}, the nonzero coefficient of {target}.', r'\frac{'+sp.latex(a*symbol)+'}{'+sp.latex(a)+'}='+r'\frac{'+sp.latex(-b)+'}{'+sp.latex(a)+'}'))
        steps.append(equation_step(symbol, answer, f'Simplify to isolate {target}.'))
        verified = sp.simplify(left.subs(symbol, answer)-right.subs(symbol, answer)) == 0
        steps.append(equation_step(sp.simplify(left.subs(symbol, answer)), sp.simplify(right.subs(symbol, answer)), f'Substitute {target} = {answer} into the original equation. Both sides agree.'))
        return dict(base, kind='parametric' if len(names)>1 else 'unique', topic='Linear equation', solution=str(answer), solutions=[str(answer)], verified=bool(verified))
    a, b, c = (polynomial.nth(i) for i in (2, 1, 0))
    if any(coef.free_symbols for coef in (a,b,c)):
        raise MathError('Parameterized quadratic equations are outside Phase 1.')
    discriminant = sp.simplify(b*b-4*a*c)
    steps.append(equation_step(difference, sp.Integer(0), 'Subtract the right side from both sides and collect powers of the variable.'))
    steps.append(step(f'D = ({b})^2 - 4*({a})*({c}) = {discriminant}', 'Calculate the discriminant D = b² − 4ac.', 'D='+sp.latex(discriminant)))
    if discriminant.is_negative:
        steps.append(step('No real solutions', 'The discriminant is negative, so there are no real roots. Complex-number solving is a later phase.'))
        return dict(base, kind='none', topic='Quadratic equation')
    if discriminant.is_nonnegative is not True:
        raise MathError('Could not establish the discriminant sign safely.')
    roots = sorted(set([sp.simplify((-b-sp.sqrt(discriminant))/(2*a)), sp.simplify((-b+sp.sqrt(discriminant))/(2*a))]), key=sp.default_sort_key)
    factored = sp.factor(difference)
    if factored != difference:
        steps.append(equation_step(factored, sp.Integer(0), 'Factor the polynomial. A product is zero when at least one factor is zero.'))
    steps.append(step(f'{target} = (-({b}) ± sqrt({discriminant})) / (2*({a}))', 'Apply the quadratic formula to obtain all real roots.', sp.latex(symbol)+r'=\frac{-('+sp.latex(b)+r')\pm\sqrt{'+sp.latex(discriminant)+r'}}{2('+sp.latex(a)+')}'))
    verified = True
    for root in roots:
        steps.append(equation_step(symbol, root, 'Simplify this exact root.'))
        l, r = sp.simplify(left.subs(symbol, root)), sp.simplify(right.subs(symbol, root))
        verified = verified and sp.simplify(l-r) == 0
        steps.append(equation_step(l, r, f'Substitute {target} = {root} into the original equation. Both sides agree.'))
    return dict(base, kind='unique' if len(roots)==1 else 'multiple', topic='Quadratic equation', solution=str(roots[0]) if len(roots)==1 else None, solutions=[str(r) for r in roots], verified=bool(verified))


def analyze(steps):
    original = solve(steps[0])
    if original['kind'] in ('expression', 'underdetermined', 'parametric'):
        raise MathError('Step checking currently requires single-variable linear or quadratic equations.')
    variable = original['variable']
    for index, text in enumerate(steps[1:], 1):
        try:
            current = solve(text, variable)
            equivalent = current['kind'] == original['kind'] and current['solutions'] == original['solutions']
            message = 'This step changes the solution set. Apply the same reversible operation to both sides.'
            error_code = 'changed_solution'
            if not equivalent:
                prev_left, prev_right = sides(steps[index-1])
                next_left, next_right = sides(text)
                if (prev_left == next_left) != (prev_right == next_right):
                    message = 'Only one side changed. Keep the equation balanced by applying the same operation to both sides.'
                    error_code = 'one_side_changed'
        except MathError as exc:
            equivalent, message = False, str(exc)
            error_code = 'division_by_zero' if 'zero' in message else 'unsupported_input'
        if not equivalent:
            return dict(valid=False, first_incorrect_step=index+1, message=message, error_code=error_code, corrected=original)
    return dict(valid=True, first_incorrect_step=None, message='Every equation has the same solution set. Nicely done!', error_code=None, corrected=original)
