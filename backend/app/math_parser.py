"""Strict mathematical grammar. No Python evaluation or string-to-SymPy parsing."""
import re
from dataclasses import dataclass
import sympy as sp

VARIABLES = frozenset(('x y z n a b c t u v theta alpha beta').split())

class MathError(ValueError):
    pass

@dataclass(frozen=True)
class Node:
    kind: str
    value: str = ''
    children: tuple = ()

class Parser:
    def __init__(self, source):
        if not source or len(source) > 200:
            raise MathError('Use an expression of 1–200 characters.')
        source = source.replace('−', '-').replace('×', '*').replace('÷', '/')
        source = source.replace('²', '^2').replace('³', '^3').replace('√', 'sqrt ')
        self.tokens = []
        self.names = set()
        pos = 0
        pattern = re.compile(r'\s+|\d+(?:\.\d+)?(?:[eE][+-]?\d+)?|[A-Za-z]+|\*\*|[+*/()^\-]')
        while pos < len(source):
            match = pattern.match(source, pos)
            if not match:
                raise MathError('Unsupported syntax. Use variables, numbers, + - * /, powers, parentheses or sqrt().')
            token = match.group()
            pos = match.end()
            if not token.isspace():
                self.tokens.append(token)
        if len(self.tokens) > 80:
            raise MathError('Use at most 80 mathematical tokens.')
        self.i = 0
        self.nodes = 0

    def node(self, kind, value='', children=()):
        self.nodes += 1
        if self.nodes > 100:
            raise MathError('This expression is too complex.')
        return Node(kind, value, children)

    def peek(self):
        return self.tokens[self.i] if self.i < len(self.tokens) else ''

    def take(self):
        t = self.peek()
        self.i += 1
        return t

    def parse(self):
        result = self.add(0)
        if self.peek():
            raise MathError('Unexpected symbol or missing operator.')
        return result

    def add(self, depth):
        result = self.multiply(depth)
        while self.peek() in ('+', '-'):
            op = self.take()
            result = self.node(op, children=(result, self.multiply(depth)))
        return result

    def multiply(self, depth):
        result = self.unary(depth)
        while True:
            token = self.peek()
            if token in ('*', '/'):
                self.take()
                result = self.node(token, children=(result, self.unary(depth)))
            elif token and (token == '(' or token[0].isalpha() or token[0].isdigit()):
                if token[0].isdigit() and self.tokens[self.i-1][0].isdigit():
                    raise MathError('Put an operator between numbers.')
                result = self.node('*', children=(result, self.unary(depth)))
            else:
                return result

    def unary(self, depth):
        if depth > 15:
            raise MathError('Too many nested operations (maximum depth 15).')
        if self.peek() in ('+', '-'):
            return self.node('sign', self.take(), (self.unary(depth+1),))
        return self.power(depth)

    def power(self, depth):
        result = self.atom(depth)
        if self.peek() in ('^', '**'):
            self.take()
            sign = self.take() if self.peek() in ('+', '-') else ''
            exponent = self.take()
            if not exponent.isdigit() or len(exponent) > 1 or not 0 <= int(exponent) <= 6:
                raise MathError('Phase 1 supports integer powers from -6 to 6, without power towers.')
            if self.peek() in ('^', '**'):
                raise MathError('Power towers are not supported.')
            result = self.node('power', sign+exponent, (result,))
        return result

    def atom(self, depth):
        if depth > 15:
            raise MathError('Too many nested parentheses.')
        token = self.take()
        if token == '(':
            result = self.add(depth+1)
            if self.take() != ')':
                raise MathError('Close each parenthesis.')
            return result
        if token in VARIABLES:
            self.names.add(token)
            if len(self.names) > 3:
                raise MathError('Use at most three distinct variables in Phase 1.')
            return self.node('symbol', token)
        if token == 'sqrt':
            # The radical consumes one atom: write sqrt(x + 4) for a sum.
            return self.node('sqrt', children=(self.atom(depth+1),))
        if re.fullmatch(r'\d+(?:\.\d+)?(?:[eE][+-]?\d+)?', token):
            parts = re.split('[eE]', token)
            if len(parts[0]) > 12 or (len(parts) == 2 and (len(parts[1].lstrip('+-')) > 2 or abs(int(parts[1])) > 12)):
                raise MathError('Number too large: use at most 12 digits and scientific exponents between -12 and 12.')
            return self.node('number', token)
        if token.isalpha():
            raise MathError(f'{token} is not supported in Phase 1. Use x, y, z, n, a, b, c, t, u, v, theta, alpha, beta or sqrt().')
        raise MathError('Incomplete or invalid mathematical expression.')


def build(node):
    if node.kind == 'number':
        return sp.Rational(node.value)
    if node.kind == 'symbol':
        return sp.Symbol(node.value, real=True)
    args = [build(c) for c in node.children]
    if node.kind == 'sign':
        result = args[0] if node.value == '+' else -args[0]
    elif node.kind == 'sqrt':
        if args[0].free_symbols:
            raise MathError('Phase 1 supports numeric square roots. Roots containing variables need domain tracking in a later phase.')
        if args[0].is_negative:
            raise MathError('Complex square roots are outside Phase 1; this solver uses real numbers.')
        result = sp.sqrt(args[0])
    elif node.kind in ('/', 'power'):
        exponent = int(node.value) if node.kind == 'power' else -1
        base = args[0] if node.kind == 'power' else args[1]
        if exponent <= 0 and base == 0:
            raise MathError('Division by zero or zero to a nonpositive power is not defined.')
        if exponent == 0 and base.free_symbols:
            raise MathError('Zero powers of variable expressions require a nonzero-base condition; use a positive integer power in Phase 1.')
        if exponent < 0 and base.free_symbols:
            raise MathError('Variable denominators are outside Phase 1; their domain restrictions require a later handler.')
        result = base ** exponent
        if node.kind == '/':
            result *= args[0]
    elif node.kind == '+':
        result = args[0] + args[1]
    elif node.kind == '-':
        result = args[0] - args[1]
    else:
        result = args[0] * args[1]
    if sp.count_ops(result) > 150:
        raise MathError('Expression exceeds the calculation complexity limit.')
    for number in result.atoms(sp.Rational):
        if abs(int(number.p)).bit_length() > 512 or int(number.q).bit_length() > 512:
            raise MathError('Number exceeds the calculation size limit.')
    if result.free_symbols and result.is_polynomial(*result.free_symbols):
        poly = sp.Poly(result, *sorted(result.free_symbols, key=str))
        if poly.total_degree() > 6 or len(poly.terms()) > 100:
            raise MathError('Phase 1 supports polynomial expressions of total degree at most 6 and at most 100 terms.')
    return result


def parse(source):
    parser = Parser(source)
    tree = parser.parse()
    return build(tree), parser.names
