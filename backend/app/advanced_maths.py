"""Bounded Phase 2 handlers. All inputs enter the shared strict parser."""
import math
import re
import sympy as sp
from .math_parser import parse, parse_defined, MathError
from .maths import step, equation_step


def result(kind, topic, names, steps, answer=None, **extra):
    return dict(kind=kind, topic=topic, variables=names, variable=names[0] if len(names)==1 else None,
                domain='real', solution=answer, solutions=[], steps=steps, verified=True,
                latex=steps[-1].get('latex') or '', **extra)


def solve_system(source, variable=None):
    parts = re.split(r';|\n|\s+with\s+', source)
    if not 2 <= len(parts) <= 3 or any(not part.strip() for part in parts):
        raise MathError('Enter two or three linear equations separated by semicolons, for example 2x+y=7; x-y=2.')
    parsed, names = [], set()
    for part in parts:
        if part.count('=') != 1 or any(c in part for c in '<>≤≥'):
            raise MathError('Each system line must be one linear equation with one equals sign.')
        left, ln = parse(part.split('=')[0])
        right, rn = parse(part.split('=')[1])
        names |= ln | rn
        parsed.append((left, right))
    names = sorted(names)
    if not 1 <= len(names) <= 3:
        raise MathError('Systems support one to three variables.')
    if variable and variable not in names:
        raise MathError('The selected variable does not occur in this system.')
    symbols = [sp.Symbol(name, real=True) for name in names]
    try:
        a, b = sp.linear_eq_to_matrix([l-r for l,r in parsed], symbols)
    except (ValueError, sp.PolynomialError):
        raise MathError('Only linear systems are supported; products and powers of unknowns need a later solver.')
    if any(v.is_Rational is not True for v in list(a)+list(b)):
        raise MathError('Linear systems currently require rational numeric coefficients (integers, fractions or decimals).')
    steps = [equation_step(l, r, f'Read equation {i+1}.') for i,(l,r) in enumerate(parsed)]
    matrix = a.row_join(b)
    steps.append(step('Augmented matrix', 'Write the coefficients and constants in an augmented matrix, with columns '+', '.join(names)+'.', sp.latex(matrix)))
    row = 0
    pivots = []
    for col in range(len(symbols)):
        pivot = next((i for i in range(row, matrix.rows) if matrix[i,col] != 0), None)
        if pivot is None:
            continue
        if pivot != row:
            matrix.row_swap(pivot, row)
            steps.append(step('Swap rows', f'Swap equations {pivot+1} and {row+1}; this preserves the solution set.', sp.latex(matrix)))
        coefficient = matrix[row,col]
        if coefficient != 1:
            matrix.row_op(row, lambda value, j: value/coefficient)
            steps.append(step('Normalize pivot', f'Divide row {row+1} by {coefficient}.', sp.latex(matrix)))
        for other in range(matrix.rows):
            if other != row and matrix[other,col] != 0:
                factor = matrix[other,col]
                matrix.row_op(other, lambda value, j: value-factor*matrix[row,j])
                steps.append(step('Eliminate a variable', f'Subtract {factor} times row {row+1} from row {other+1}.', sp.latex(matrix)))
        pivots.append((row,col))
        row += 1
        if row == matrix.rows:
            break
    if any(all(matrix[i,j]==0 for j in range(len(symbols))) and matrix[i,-1]!=0 for i in range(matrix.rows)):
        steps.append(step('No solution', 'A row says zero equals a nonzero constant, so the system is inconsistent.', r'\varnothing'))
        return result('none','Linear system',names,steps)
    pivot_cols = {col for _,col in pivots}
    values = {s:s for i,s in enumerate(symbols) if i not in pivot_cols}
    for row,col in pivots:
        values[symbols[col]] = sp.simplify(matrix[row,-1]-sum(matrix[row,j]*symbols[j] for j in range(len(symbols)) if j not in pivot_cols))
    assignments = {str(s):str(values[s]) for s in symbols}
    answer = ', '.join(f'{s} = {values[s]}' for s in symbols)
    latex = r',\quad '.join(sp.latex(s)+'='+sp.latex(values[s]) for s in symbols)
    free = [str(s) for s in symbols if s in values and values[s] == s]
    steps.append(step(answer, 'Read the unique solution.' if not free else 'There are infinitely many solutions. Free real variables: '+', '.join(free)+'.', latex))
    for i,(left,right) in enumerate(parsed):
        l, r = sp.simplify(left.subs(values, simultaneous=True)), sp.simplify(right.subs(values, simultaneous=True))
        if sp.simplify(l-r) != 0:
            raise MathError('Could not verify the computed system solution.')
        steps.append(equation_step(l,r,f'Substitute the values into original equation {i+1}. Both sides agree.'))
    return result('parametric' if free else 'system','Linear system',names,steps,answer,assignments=assignments)


def solve_inequality(source, variable=None):
    source = source.replace('≤','<=').replace('≥','>=')
    parts = re.split(r'(<=|>=|<|>)', source)
    if len(parts) != 3 or '=' in parts[0] or '=' in parts[2]:
        raise MathError('Enter one inequality; chained or combined inequalities are not supported yet.')
    left, ln = parse(parts[0]); right, rn = parse(parts[2])
    names = sorted(ln|rn)
    if len(names)>1 or (variable and names and variable not in names):
        raise MathError('Inequalities currently support one variable. Select that variable or use auto-detect.')
    target = sp.Symbol(variable or (names[0] if names else 'x'), real=True)
    difference = sp.expand(left-right)
    if not difference.is_polynomial(target):
        raise MathError('Inequalities support linear or quadratic polynomials only.')
    poly = sp.Poly(difference,target)
    if poly.degree()>2 or any(c.is_Rational is not True for c in poly.all_coeffs()):
        raise MathError('Inequalities require degree at most two and rational coefficients.')
    relation = {'<':sp.Lt,'<=':sp.Le,'>':sp.Gt,'>=':sp.Ge}[parts[1]]
    original = relation(left,right)
    normalized = relation(difference,0)
    steps = [step(source,'Read the inequality over real numbers.',sp.latex(original)),step(str(normalized),'Subtract the right side from both sides and collect like terms.',sp.latex(normalized))]
    if poly.degree()==1:
        a,b = poly.nth(1),poly.nth(0)
        boundary = -b/a
        op = {'<':'>','<=':'>=','>':'<','>=':'<='}[parts[1]] if a<0 else parts[1]
        isolated = {'<':sp.Lt,'<=':sp.Le,'>':sp.Gt,'>=':sp.Ge}[op](target,boundary)
        steps.append(step(str(isolated), f'Divide by {a}. '+('Reverse the inequality because this number is negative.' if a<0 else 'Keep the inequality direction because this number is positive.'),sp.latex(isolated)))
    elif poly.degree()==2:
        roots = sp.solveset(difference,target,domain=sp.S.Reals)
        steps.append(step(str(roots),'Find the real zeros. These divide the number line into intervals; determine the polynomial sign on each interval.',sp.latex(roots)))
        steps.append(step(str(sp.factor(difference)),'Factor where possible. Include zero endpoints only for ≤ or ≥.',sp.latex(sp.factor(difference))))
    solution = sp.solve_univariate_inequality(normalized,target,relational=False)
    readable = 'No real solutions' if solution is sp.S.EmptySet else 'All real numbers' if solution == sp.S.Reals else str(solution)
    steps.append(step(readable,'The resulting real solution set. Parentheses exclude endpoints; square brackets include endpoints.',sp.latex(solution)))
    return result('inequality','Polynomial inequality',names,steps,readable)


def sample_graph(source, minimum=-5, maximum=5):
    if not math.isfinite(minimum) or not math.isfinite(maximum) or not -10<=minimum<maximum<=10:
        raise MathError('Choose a graph interval within -10 to 10, with minimum less than maximum.')
    if source.strip().startswith('y=') or source.strip().startswith('y ='):
        source = source.split('=',1)[1]
    value, names, conditions = parse_defined(source)
    x = sp.Symbol('x',real=True)
    if names-{'x'}:
        raise MathError('Function graphs currently use x only; other variables require numerical values.')
    # Bounded affine function arguments make detection of tangent poles reliable at this sampling density.
    guards = []
    for func in sp.Tuple(value, *conditions).atoms(sp.sin,sp.cos,sp.tan,sp.log,sp.exp):
        arg = func.args[0]
        if arg.free_symbols:
            if not arg.is_polynomial(x) or sp.Poly(arg,x).degree()>1 or abs(float(arg.coeff(x)))>10:
                raise MathError('Graph function arguments must be affine in x with slope magnitude at most 10.')
    for condition in conditions:
        if isinstance(condition, sp.Unequality):
            guards.append(condition.lhs)
    segments, segment, previous_guards = [], [], None
    for index in range(401):
        at = sp.Rational(str(minimum))+(sp.Rational(str(maximum))-sp.Rational(str(minimum)))*index/400
        valid = all(c.subs(x,at) == sp.S.true for c in conditions)
        g = [float(guard.subs(x,at).evalf()) for guard in guards]
        if any(abs(v)<1e-8 for v in g): valid=False
        numeric = value.subs(x,at).evalf() if valid else None
        valid = valid and numeric.is_real is True and numeric.is_finite is True and abs(numeric)<=10000
        crossed = previous_guards is not None and any(a*b<0 for a,b in zip(previous_guards,g))
        if not valid or crossed:
            if segment: segments.append(segment)
            segment=[]
        if valid:
            segment.append({'x':float(at),'y':float(numeric)})
        previous_guards = g if valid else None
    if segment: segments.append(segment)
    if not segments:
        raise MathError('No finite real graph points in this interval. Check the domain or choose another interval.')
    return {'segments':segments,'latex':sp.latex(value),'domain_conditions':[str(c) for c in conditions],
            'note':'Approximate plot from 401 samples; radians and natural logarithms. Values above magnitude 10,000 are omitted. Gaps mark undefined or clipped regions.'}
