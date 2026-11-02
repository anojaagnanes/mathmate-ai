"""Bounded geometry, descriptive statistics and finite probability handlers."""
import re
import sympy as sp
from sympy.geometry import Point, Polygon, Circle
from .math_parser import MathError, parse
from .linear_algebra import split_items, array

GEOMETRY = {'rectangle_area', 'rectangle_perimeter', 'triangle_area', 'circle_area', 'circumference', 'hypotenuse'}
STATISTICS = {'mean', 'median', 'mode', 'variance', 'sample_variance', 'stddev'}
COUNTING = {'choose', 'permutations', 'probability'}
COMMANDS = GEOMETRY | STATISTICS | COUNTING


def number(text):
    value, names = parse(text)
    if names or value.is_Rational is not True or abs(value) > 10000:
        raise MathError('Use rational numbers of magnitude at most 10,000, without variables.')
    return value


def solve_topic(source, variable=None):
    from .maths import step
    if variable:
        raise MathError('Choose Auto-detect for geometry, statistics and probability commands.')
    match = re.fullmatch(r'\s*([a-z_]+)\s*\((.*)\)\s*', source, re.S)
    if not match or match[1] not in COMMANDS:
        raise MathError('Use a supported topic command with numeric arguments.')
    op, args = match[1], split_items(match[2])
    steps = [step(source, 'Read the supplied quantities. All calculations use exact arithmetic.')]
    diagram = None
    if op in GEOMETRY:
        expected = 1 if op in {'circle_area', 'circumference'} else 2
        if len(args) != expected:
            raise MathError(f'{op} needs {expected} positive dimension(s).')
        values = [number(arg) for arg in args]
        if any(v <= 0 for v in values):
            raise MathError('Lengths must be positive. Use the same unit for all dimensions.')
        a = values[0]; b = values[-1]
        if op.startswith('rectangle'):
            shape = Polygon(Point(0, 0), Point(a, 0), Point(a, b), Point(0, b))
            area = op == 'rectangle_area'
            answer = a*b if area else 2*(a+b)
            check = shape.area if area else shape.perimeter
            formula = r'A=l\times w' if area else r'P=2(l+w)'
            explanation = 'Multiply length by width.' if area else 'Add length and width, then double the sum.'
            labels = [f'length = {a}', f'width = {b}']; kind = 'rectangle'
        elif op == 'triangle_area':
            answer = a*b/2
            check = Polygon(Point(0, 0), Point(a, 0), Point(a/3, b)).area
            formula = r'A=\frac{1}{2}bh'; explanation = 'Multiply base by perpendicular height and divide by two. Height is not a sloping side.'
            labels = [f'base = {a}', f'perpendicular height = {b}']; kind = 'triangle'
        elif op == 'hypotenuse':
            answer = sp.sqrt(a*a+b*b)
            check = Point(0, a).distance(Point(b, 0))
            formula = r'c=\sqrt{a^2+b^2}'; explanation = 'For a right triangle, square the two perpendicular legs, add them, and take the positive square root.'
            labels = [f'leg a = {a}', f'leg b = {b}']; kind = 'right_triangle'
        else:
            shape = Circle(Point(0, 0), a)
            area = op == 'circle_area'
            answer = sp.pi*a*a if area else 2*sp.pi*a
            check = shape.area if area else shape.circumference
            formula = r'A=\pi r^2' if area else r'C=2\pi r'
            explanation = 'Use the radius, not the diameter, in the circle formula.'
            labels = [f'radius = {a}']; kind = 'circle'
        diagram = {'shape': kind, 'labels': labels, 'caption': 'Schematic, not to scale. Based on entered dimensions; no image interpretation.'}
        steps.append(step(formula, explanation, formula))
        unit = 'square units' if op.endswith('_area') else 'length units'
        steps.append(step(str(answer), f'Substitute {", ".join(str(v) for v in values)} into the formula. Result: {answer} {unit}.', sp.latex(answer)))
        verified = sp.simplify(answer-check) == 0
        steps.append(step(str(check), 'Check independently using geometric objects or distance. All dimensions must use a common unit.', sp.latex(check)))
        topic = 'Geometry · ' + unit
    elif op in STATISTICS:
        if len(args) != 1:
            raise MathError('Provide one bracketed data list, for example mean([2,4,6]).')
        entries = array(args[0])
        if not 1 <= len(entries) <= 30:
            raise MathError('Use between 1 and 30 data values.')
        values = sorted(number(v) for v in entries)
        n = len(values); total = sum(values, sp.Integer(0)); avg = total/n
        steps.append(step(str(values), f'Sort the {n} data values. Repeated values count as separate observations.', sp.latex(sp.Tuple(*values))))
        if op == 'mean':
            answer = avg
            verified = answer*n == total
            steps.append(step(str(answer), f'Add the values to get {total}, then divide by the count {n}.', sp.latex(total)+r'/'+str(n)+'='+sp.latex(answer)))
        elif op == 'median':
            answer = values[n//2] if n % 2 else (values[n//2-1]+values[n//2])/2
            verified = sum(1 for v in values if v <= answer) >= (n+1)//2 and sum(1 for v in values if v >= answer) >= (n+1)//2
            steps.append(step(str(answer), 'Select the middle value for an odd count, or average the two middle values for an even count.', sp.latex(answer)))
        elif op == 'mode':
            from collections import Counter
            counts = Counter(values); highest = max(counts.values())
            if highest == 1:
                raise MathError('Every value appears once: this data set has no mode under the repeated-value convention.')
            modes = sorted(v for v, count in counts.items() if count == highest)
            answer = sp.Tuple(*modes)
            verified = all(values.count(v) == highest for v in modes)
            steps.append(step(str(answer), f'Each listed mode occurs {highest} times, the greatest frequency. Include every tied mode.', sp.latex(answer)))
        else:
            if op == 'sample_variance' and n < 2:
                raise MathError('Sample variance needs at least two observations.')
            squared = sum((v-avg)**2 for v in values)
            denominator = n-1 if op == 'sample_variance' else n
            variance = squared/denominator
            answer = sp.sqrt(variance) if op == 'stddev' else variance
            check = (sum(v*v for v in values)-total*total/n)/denominator
            verified = sp.simplify((answer**2 if op == 'stddev' else answer)-check) == 0
            steps.append(step(str(avg), f'The mean is {avg}. Sum squared distances from the mean: {squared}.', sp.latex(squared)))
            steps.append(step(str(answer), f'Divide by {denominator} ({"sample: n−1" if op == "sample_variance" else "population: n"})'+(' and take the square root.' if op == 'stddev' else '.'), sp.latex(answer)))
        topic = 'Statistics · ' + op.replace('_', ' ')
        steps.append(step(str(answer), 'Check the result using the defining count, order or an equivalent sum-of-squares identity.', sp.latex(answer)))
    else:
        if len(args) != 2:
            raise MathError(f'{op} requires two integer arguments.')
        a, b = (number(v) for v in args)
        if any(v.is_Integer is not True or v < 0 or v > 100 for v in (a, b)):
            raise MathError('Use whole-number counts between 0 and 100.')
        if op == 'probability':
            if b == 0 or a > b:
                raise MathError('Total outcomes must be positive and favorable outcomes cannot exceed the total.')
            answer = a/b; verified = 0 <= answer <= 1 and answer*b == a
            explanation = f'Assuming {b} equally likely outcomes and {a} favorable outcomes, probability = favorable / total.'
        else:
            if b > a:
                raise MathError('The selection size cannot exceed the number of available objects.')
            product = sp.prod(a-i for i in range(int(b)))
            answer = product/sp.factorial(b) if op == 'choose' else product
            check = sp.binomial(a,b) if op == 'choose' else sp.factorial(a)/sp.factorial(a-b)
            verified = answer == check
            explanation = (f'Select {b} of {a} distinct objects without replacement. Divide the ordered product by {b}! because order does not matter.' if op == 'choose' else f'Arrange {b} of {a} distinct objects without replacement; order matters.')
        topic = 'Finite probability and counting'
        steps.append(step(str(answer), explanation, sp.latex(answer)))
        steps.append(step(str(answer), 'Check with an equivalent factorial formula or the probability bounds and outcome counts.', sp.latex(answer)))
    if not verified:
        raise MathError('The independent mathematical check did not agree; no result is returned.')
    return dict(kind='expression', topic=topic, solution=str(answer), solutions=[], variables=[], variable=None,
                domain='real', verified=True, domain_conditions=[], latex=sp.latex(answer), steps=steps, diagram=diagram)
