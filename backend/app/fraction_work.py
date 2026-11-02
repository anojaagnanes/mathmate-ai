import re
import sympy as sp
from .maths import solve, step
from .agents.practice import PracticeAgent

F=r'\d{1,4}\s*/\s*[1-9]\d{0,3}'

def fraction_review(lines):
    first=re.fullmatch(fr'\s*({F})(?:\s*\+\s*({F}))?\s*(=|<|>)\s*({F}|\d{{1,4}})\s*',lines[0])
    if not first:return None
    a=sp.Rational(first[1].replace(' ','')); b=sp.Rational(first[2].replace(' ','')) if first[2] else None
    category='addition' if b is not None else 'equivalence' if first[3]=='=' else 'comparison'
    target=a+b if b is not None else a
    rows=[];bad=None
    from .math_parser import parse_defined,MathError
    for i,line in enumerate(lines):
        if bad is not None:
            rows.append(dict(number=i+1,original=line,normalized=line,status='dependent',reason='Depends on the earlier incorrect step.'));continue
        match=re.fullmatch(r'(.+?)\s*(=|<|>)\s*(.+)',line)
        try:
            if not match: return None
            left,ln,lc=parse_defined(match[1]);right,rn,rc=parse_defined(match[3])
            if ln or rn or lc or rc or not left.is_Rational or not right.is_Rational:return None
            valid=bool({'=':left==right,'<':left<right,'>':left>right}[match[2]])
            if category!='comparison':valid=valid and left==target
        except MathError:return None
        if not valid:bad=i+1
        rows.append(dict(number=i+1,original=line,normalized=line,status='correct' if valid else 'incorrect',reason='Exact rational values agree with this statement.' if valid else 'This statement changes the value or uses an incorrect comparison.'))
    if category=='addition':
        denominator=sp.ilcm(a.q,b.q);n1=a.p*(denominator//a.q);n2=b.p*(denominator//b.q)
        expr=f'{first[1]} + {first[2]}'
        solution=solve(expr)
        solution['steps']=[step(expr,'Read the fractions being added.'),step(f'{n1}/{denominator} + {n2}/{denominator}','Use a common denominator; multiply each numerator and denominator by the same factor.'),step(f'{n1+n2}/{denominator}','Add the numerators and keep the common denominator.'),step(str(target),'Simplify the resulting fraction.',sp.latex(target))]
        message='Use a common denominator before adding the numerators. Do not add the denominators.' if bad else 'Your fraction addition is correct.'
    elif category=='equivalence':
        solution=solve(first[1]);solution['steps']=[step(first[1],'Read the fraction.'),step(str(a),'Divide numerator and denominator by the same nonzero common factor.',sp.latex(a))]
        message='Equivalent fractions have the same exact value.'
    else:
        right=sp.Rational(first[4].replace(' ',''));operator='<' if a<right else '>' if a>right else '='
        denominator=sp.ilcm(a.q,right.q)
        solution=solve(first[1]);solution.update(solution=operator,latex=f'{sp.latex(a)} {operator} {sp.latex(right)}')
        solution['steps']=[step(f'{first[1]} and {first[4]}','Compare the two fractions.'),step(f'{a.p*(denominator//a.q)}/{denominator} and {right.p*(denominator//right.q)}/{denominator}','Rewrite with a common denominator.'),step(f'{a} {operator} {right}','Compare the numerators with the common positive denominator.')]
        message='Compare fractions using the same denominator.'
    solution['topic']='Fractions'
    if bad == 1 and category == 'addition' and first[3] == '=':
        n,d=map(int,first[1].replace(' ','').split('/'))
        m,e=map(int,first[2].replace(' ','').split('/'))
        if sp.Rational(first[4].replace(' ','')) == sp.Rational(n+m,d+e):
            message='Your answer matches adding both numerators and denominators directly. That may be the mistake: denominators describe the size of each part. Make the parts equal before adding. The verified answer is '+str(target)+'.'
            rows[0]['reason']=message
    practice=PracticeAgent().generate(category)
    return dict(status='incorrect_step_detected' if bad else 'correct',lines=rows,first_incorrect_step=bad,error_category='fraction_'+category if bad else None,verified_correction=solution['steps'][-1]['equation'],corrected=solution,practice=practice,message=message,normalization_required=False,practice_category=category)
