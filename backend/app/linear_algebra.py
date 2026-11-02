"""Small rational matrices/vectors, parsed without Python evaluation."""
import re
import sympy as sp
from .math_parser import MathError, parse

COMMANDS = {'Matrix', 'Vector', 'det', 'inverse', 'transpose', 'matmul', 'matrixadd', 'dot', 'cross', 'norm'}


def split_items(text):
    stack, start, parts = [], 0, []
    for i,c in enumerate(text):
        if c in '([':
            stack.append(c)
            if len(stack)>15: raise MathError('Too many nested brackets.')
        elif c in ')]':
            if not stack or stack.pop() != {')':'(',']':'['}[c]:
                raise MathError('Match every bracket and parenthesis.')
        elif c==',' and not stack:
            parts.append(text[start:i].strip()); start=i+1
    if stack: raise MathError('Close every bracket and parenthesis.')
    parts.append(text[start:].strip())
    if any(not p for p in parts): raise MathError('Empty entries are not allowed.')
    return parts


def scalar(text):
    value,names=parse(text)
    if names or value.is_Rational is not True:
        raise MathError('Matrix and vector entries must be integers, decimals or fractions, without variables.')
    return value


def array(text):
    text=text.strip()
    if not text.startswith('[') or not text.endswith(']'):
        raise MathError('Use square brackets for rows or vectors.')
    return split_items(text[1:-1])


def matrix(text):
    if text.startswith('Matrix(') and text.endswith(')'): text=text[7:-1]
    rows=array(text)
    if not 1<=len(rows)<=3: raise MathError('Matrices support one to three rows and columns.')
    parsed=[array(row) for row in rows]
    if not 1<=len(parsed[0])<=3 or any(len(row)!=len(parsed[0]) for row in parsed):
        raise MathError('Use a rectangular matrix with one to three columns in every row.')
    return sp.Matrix([[scalar(v) for v in row] for row in parsed])


def vector(text):
    if text.startswith('Vector(') and text.endswith(')'): text=text[7:-1]
    values=array(text)
    if len(values) not in (2,3): raise MathError('Vectors must have two or three components.')
    return sp.Matrix([scalar(v) for v in values])


def determinant_steps(a,steps):
    from .maths import step
    if a.rows!=a.cols: raise MathError('A determinant or inverse requires a square matrix.')
    terms=[]
    for j in range(a.cols):
        minor=a.minor_submatrix(0,j).det() if a.rows>1 else sp.Integer(1)
        term=(-1)**j*a[0,j]*minor
        terms.append(term)
        steps.append(step(str(term),f'First-row cofactor {j+1}: multiply {a[0,j]} by minor determinant {minor} and sign {(-1)**j}.',sp.latex(sp.Mul((-1)**j,a[0,j],minor,evaluate=False))+'='+sp.latex(term)))
    value=sum(terms,sp.Integer(0))
    if value!=a.det(): raise MathError('Determinant verification failed.')
    steps.append(step(str(value),'Add the cofactor contributions to obtain the determinant.',sp.latex(value)))
    return value


def solve_linear_algebra(source,variable=None):
    from .maths import step
    if variable: raise MathError('Choose Auto-detect for numeric matrix and vector calculations.')
    call=re.fullmatch(r'\s*([A-Za-z]+)\s*\((.*)\)\s*',source,re.S)
    if not call or call.group(1) not in COMMANDS:
        raise MathError('Use Matrix, Vector, det, inverse, transpose, matmul, matrixadd, dot, cross or norm with bracketed numeric entries.')
    op=call.group(1); args=split_items(call.group(2))
    expected=2 if op in ('matmul','matrixadd','dot','cross') else 1
    if len(args)!=expected: raise MathError(f'{op} requires exactly {expected} argument(s).')
    is_vector=op in ('Vector','dot','cross','norm')
    values=[(vector if is_vector else matrix)(arg) for arg in args]
    steps=[step(str(v),f'Read {"vector" if is_vector else "matrix"} {i+1} with exact rational entries.',sp.latex(v)) for i,v in enumerate(values)]
    a=values[0]
    verified=True
    if op in ('Matrix','Vector'):
        answer=a
        steps.append(step(str(answer),'The entries have been parsed as exact rational numbers.',sp.latex(answer)))
    elif op=='det':
        answer=determinant_steps(a,steps)
    elif op=='inverse':
        d=determinant_steps(a,steps)
        if d==0: raise MathError('This matrix is singular: its determinant is zero, so an inverse does not exist.')
        adj=a.adjugate()
        steps.append(step(str(adj),'Form the adjugate by transposing the cofactor matrix.',sp.latex(adj)))
        answer=adj/d
        steps.append(step(str(answer),f'Divide every adjugate entry by the nonzero determinant {d}.',sp.latex(answer)))
        check=a*answer
        verified=check==sp.eye(a.rows) and answer*a==sp.eye(a.rows)
        steps.append(step(str(check),'Verify: multiplying the original matrix and its inverse in either order gives the identity.',sp.latex(check)))
    elif op=='transpose':
        answer=a.T; verified=answer.T==a
        steps.append(step(str(answer),'Swap rows and columns. Transposing the result again recovers the original matrix.',sp.latex(answer)))
    elif op in ('matmul','matrixadd'):
        b=values[1]
        if op=='matrixadd':
            if a.shape!=b.shape: raise MathError('Matrix addition requires equal dimensions.')
            answer=a+b; verified=answer-b==a
            steps.append(step(str(answer),'Add corresponding entries. Check by subtracting the second matrix.',sp.latex(answer)))
        else:
            if a.cols!=b.rows: raise MathError('Matrix multiplication requires the first column count to equal the second row count.')
            answer=sp.zeros(a.rows,b.cols)
            for i in range(a.rows):
                for j in range(b.cols):
                    terms=[a[i,k]*b[k,j] for k in range(a.cols)]
                    answer[i,j]=sum(terms)
                    expression='+'.join('('+sp.latex(a[i,k])+')('+sp.latex(b[k,j])+')' for k in range(a.cols))
                    steps.append(step(str(answer[i,j]),f'Entry ({i+1}, {j+1}): multiply matching entries of row {i+1} and column {j+1}, then add.',expression+'='+sp.latex(answer[i,j])))
            verified=answer==a*b
            steps.append(step(str(answer),'Collect the computed entries into the product matrix.',sp.latex(answer)))
    elif op=='dot':
        b=values[1]
        if len(a)!=len(b): raise MathError('Dot products require vectors of equal length.')
        terms=[a[i]*b[i] for i in range(len(a))]
        answer=sum(terms); verified=answer==a.dot(b)
        steps.append(step(str(answer),'Multiply corresponding components and add. The dot product is a scalar.', '+'.join('('+sp.latex(a[i])+')('+sp.latex(b[i])+')' for i in range(len(a)))+'='+sp.latex(answer)))
    elif op=='cross':
        b=values[1]
        if len(a)!=3 or len(b)!=3: raise MathError('Cross products require two three-dimensional vectors.')
        answer=sp.Matrix([a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]])
        for i,(j,k) in enumerate(((1,2),(2,0),(0,1))):
            steps.append(step(str(answer[i]),f'Component {i+1}: use the cyclic cross-product rule; the order of the two vectors matters.',f'({sp.latex(a[j])})({sp.latex(b[k])})-({sp.latex(a[k])})({sp.latex(b[j])})={sp.latex(answer[i])}'))
        verified=answer==a.cross(b) and answer.dot(a)==0 and answer.dot(b)==0
        steps.append(step(str(answer),'Collect the components. Check that the result is perpendicular to both input vectors (the zero vector is allowed).',sp.latex(answer)))
    else:
        square=sum(v*v for v in a); answer=sp.sqrt(square)
        verified=sp.simplify(answer**2-square)==0 and answer.is_nonnegative
        steps.append(step(str(square),'Square each component and add.', '+'.join('('+sp.latex(v)+')^2' for v in a)+'='+sp.latex(square)))
        steps.append(step(str(answer),'Take the nonnegative square root. Squaring this length recovers the sum of squares.',sp.latex(answer)))
    if not verified: raise MathError('The matrix or vector result could not be verified.')
    return dict(kind='linear_algebra',topic='Vector calculation' if is_vector else 'Matrix calculation',
                variable=None,variables=[],solution=str(answer),solutions=[],domain='real',verified=True,
                latex=sp.latex(answer),steps=steps)
