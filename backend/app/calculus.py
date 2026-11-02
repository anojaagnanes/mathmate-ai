"""Polynomial calculus through an explicit command grammar and existing safe parser."""
import re
import sympy as sp
from .math_parser import VARIABLES, MathError, parse_defined


def command(source):
    derivative = re.fullmatch(r'\s*d/d([A-Za-z]+)\s*\((.*)\)\s*', source, flags=re.S)
    if derivative:
        return 'diff', derivative.group(2), derivative.group(1)
    call = re.fullmatch(r'\s*(diff|integrate)\s*\((.*)\)\s*', source, flags=re.S)
    if not call:
        raise MathError('Use diff(expression, variable) or integrate(expression, variable).')
    body = call.group(2)
    depth, commas = 0, []
    for i, char in enumerate(body):
        if char == '(': depth += 1
        elif char == ')': depth -= 1
        elif char == ',' and depth == 0: commas.append(i)
        if not 0 <= depth <= 15:
            raise MathError('Unbalanced or overly nested calculus input.')
    if depth != 0 or len(commas) != 1:
        raise MathError('Provide exactly an expression and a variable, for example diff(x^3, x). Higher derivatives and definite integrals are not supported yet.')
    pos = commas[0]
    return call.group(1), body[:pos].strip(), body[pos+1:].strip()


def solve_calculus(source, selected_variable=None):
    from .maths import step
    operation, text, name = command(source)
    if name not in VARIABLES:
        raise MathError('Choose a supported calculus variable such as x, y, n or theta.')
    if selected_variable and selected_variable != name:
        raise MathError('The variable selector differs from the calculus command. Choose auto-detect or the same variable.')
    value, names, conditions = parse_defined(text)
    symbol = sp.Symbol(name, real=True)
    if names - {name}:
        raise MathError('This milestone supports one-variable polynomials, not partial derivatives or symbolic parameters.')
    if conditions or not value.is_polynomial(symbol):
        raise MathError('Calculus currently supports polynomials of degree at most 6. Trigonometric, logarithmic, radical and rational-function calculus require a later handler.')
    polynomial = sp.Poly(value, symbol)
    if polynomial.degree() > 6 or any(c.is_Rational is not True for c in polynomial.all_coeffs()):
        raise MathError('Calculus supports polynomial degree at most 6 with integer, decimal or fractional coefficients.')
    derivative = operation == 'diff'
    original_latex = (r'\frac{d}{d '+sp.latex(symbol)+'}\\left('+sp.latex(value)+r'\right)' if derivative else r'\int '+sp.latex(value)+r'\,d'+sp.latex(symbol))
    steps = [step(source, ('Differentiate' if derivative else 'Integrate')+' the polynomial with respect to '+name+'.', original_latex)]
    parts = []
    for (power,), coefficient in polynomial.terms():
        term = coefficient*symbol**power
        if derivative:
            transformed = coefficient*power*symbol**(power-1) if power else sp.Integer(0)
            explanation = ('The derivative of a constant is zero.' if power == 0 else f'Power rule: multiply the coefficient {coefficient} by exponent {power}, then reduce the exponent by one.')
            latex = r'\frac{d}{d '+sp.latex(symbol)+'}\\left('+sp.latex(term)+r'\right)='+sp.latex(transformed)
        else:
            transformed = coefficient*symbol**(power+1)/sp.Integer(power+1)
            explanation = f'Integration power rule: increase exponent {power} to {power+1} and divide the coefficient by {power+1}.'
            latex = r'\int '+sp.latex(term)+r'\,d'+sp.latex(symbol)+'='+sp.latex(transformed)
        parts.append(transformed)
        steps.append(step(str(transformed), explanation, latex))
    answer = sp.expand(sum(parts))
    if derivative:
        verified = sp.simplify(answer-sp.diff(value, symbol)) == 0
        solution, latex = str(answer), sp.latex(answer)
        steps.append(step(solution, 'Combine the differentiated terms. The result is '+solution+'.', latex))
        steps.append(step(solution, 'Check: an independent differentiation of the original polynomial obtains the same expression.', latex))
    else:
        verified = sp.simplify(sp.diff(answer, symbol)-value) == 0
        solution, latex = str(answer)+' + C', sp.latex(answer)+'+C'
        steps.append(step(solution, 'Combine the terms and add one arbitrary real constant C. Every value of C gives an antiderivative.', latex))
        steps.append(step(str(value), 'Check: differentiate the result. The derivative of C is zero, and the original polynomial is recovered.', r'\frac{d}{d '+sp.latex(symbol)+'}\\left('+latex+r'\right)='+sp.latex(value)))
    if not verified:
        raise MathError('The calculus result could not be verified.')
    return dict(kind='calculus', topic='Polynomial derivative' if derivative else 'Polynomial integral',
                variable=name, variables=[name], solution=solution, solutions=[], domain='real',
                domain_conditions=[], verified=True, latex=latex, steps=steps)
