"""Bounded checking of reviewed linear work and numeric equalities; no text evaluation."""
import re
import sympy as sp
from .math_parser import MathError, parse_defined


def normalize_line(raw):
    text = re.sub(r'^\s*(?:Step\s+\d+\s*[:.)]|\d+[.)]\s+|[IVX]+[.)]\s+)', '', raw, flags=re.I).strip()
    for ta, en in {'௦': '0', '௧': '1', '௨': '2', '௩': '3', '௪': '4', '௫': '5', '௬': '6', '௭': '7', '௮': '8', '௯': '9'}.items():
        text = text.replace(ta, en)
    for old,new in [('−','-'),('–','-'),('×','*'),('÷','/'),('²','^2'),('³','^3'),('π','pi')]:
        text = text.replace(old,new)
    # Only simple flat LaTeX fractions; never guess nested/OCR notation.
    text = re.sub(r'\\frac\{([0-9]+)\}\{([0-9]+)\}', r'(\1)/(\2)', text)
    return text


def review_work(raw):
    from .maths import solve
    if not 1 <= len(raw) <= 30 or any(len(line)>200 for line in raw):
        raise MathError('Use 1–30 lines, with at most 200 characters per line.')
    normalized=[normalize_line(line) for line in raw]
    rows=[dict(number=i+1,original=line,normalized=normalized[i],status='unverified',reason='Not checked yet.') for i,line in enumerate(raw)]
    result=dict(status='unable_to_verify',lines=rows,first_incorrect_step=None,error_category=None,
                verified_correction=None,corrected=None,practice=None,message='',normalization_required=normalized!=raw)
    if normalized!=raw:
        result.update(status='review_required',message='Review the normalized notation before checking. Your original text is preserved.')
        return result
    # A sequence definition is not the product T*n. Use only an explicitly
    # supplied numeric instance, and ask the student to approve the model.
    sides=normalized[0].split('=')
    if len(sides)==2 and any(re.fullmatch(r'T_?n',side.strip()) for side in sides):
        formula=next(side.strip() for side in sides if not re.fullmatch(r'T_?n',side.strip())) if not all(re.fullmatch(r'T_?n',side.strip()) for side in sides) else ''
        if formula and len(normalized)>1 and normalized[1].count('=')==1:
            try:
                expression,names,conditions=parse_defined(formula)
                second=normalized[1].split('=')
                for candidate,value in (second,second[::-1]):
                    model,_,mc=parse_defined(candidate);term,tn,tc=parse_defined(value)
                    if names=={'n'} and not conditions and not mc and not tn and not tc and term.is_real and term.is_finite and sp.simplify(expression-model)==0:
                        rows[0]['normalized']=normalized[1]
                        result.update(status='review_required',normalization_required=True,message=f'T_n denotes the nth term. Your next line supplies its value as {term}. Confirm using that numeric equation as the starting problem; the original sequence formula is preserved.')
                        return result
            except MathError:
                pass
        result['message']='This is a sequence formula. Include the numeric term equation (for example, the value given in your question) before its working. No term value has been guessed.'
        return result
    from .fraction_work import fraction_review
    fraction_result=fraction_review(normalized)
    if fraction_result is not None:return fraction_result
    parsed=[]
    for i,text in enumerate(normalized):
        try:
            if '?' in text:raise MathError('This line contains an uncertain symbol. Compare it with the image and edit it.')
            if text.count('=')!=1:raise MathError('Enter one equality on this line. Separate questions and explanations from mathematical steps.')
            left,ln,lc=parse_defined(text.split('=')[0]);right,rn,rc=parse_defined(text.split('=')[1])
            names=ln|rn
            if lc or rc:raise MathError('Variable denominators or domain restrictions need manual review; no mistake is inferred.')
            parsed.append((left,right,names))
        except MathError as exc:
            rows[i].update(status='uncertain',reason=str(exc))
            result['message']=f'Please review line {i+1}. It cannot yet be verified reliably.'
            return result
    names=set().union(*(p[2] for p in parsed))
    if len(names)>1:
        result['message']='Check one single-variable problem at a time. Select the relevant lines from your document.'
        return result
    if not names:
        for i,(left,right,_) in enumerate(parsed):
            valid=sp.simplify(left-right)==0
            rows[i].update(status='correct' if valid else 'incorrect',reason='Both sides have the same exact value.' if valid else 'The two sides have different values.')
            if not valid and result['first_incorrect_step'] is None:result['first_incorrect_step']=i+1
        result.update(status='correct' if result['first_incorrect_step'] is None else 'incorrect_step_detected',message='Each numeric equality was checked independently; these may be separate calculations.')
        return result
    variable=next(iter(names));symbol=sp.Symbol(variable,real=True)
    for i,(left,right,_) in enumerate(parsed):
        if not all(value.is_polynomial(symbol) and sp.degree(value,symbol)<=1 for value in (left,right)):
            rows[i].update(status='unverified',reason='This checker supports linear transformations. Quadratic solving is available in Learning Studio, but this working is not verified here.')
            result['message']=rows[i]['reason'];return result
    original=solve(normalized[0],variable)
    if original['kind']!='unique':
        result['message']='This lesson currently requires a linear equation with one unique solution.';return result
    result['corrected']=original
    rows[0].update(status='starting_equation',reason='Original equation; the starting point for comparison.')
    target=original['solutions']
    for i in range(1,len(rows)):
        current=solve(normalized[i],variable)
        if current['kind']=='unique' and current['solutions']==target:
            rows[i].update(status='equivalent',reason='Equivalent linear equation with the same unique solution. This checks the equation, not an unstated operation.');continue
        reason='This line changes or loses the original solution. Apply the same reversible operation to both sides.'
        category='changed_solution';correction=None
        pl,pr,_=parsed[i-1];nl,nr,_=parsed[i];constant=pl.subs(symbol,0)
        if constant!=0 and sp.simplify(nl-(pl-constant))==0 and sp.simplify(nr-(pr+constant))==0:
            category='inverse_operation';correction=f'{pl-constant} = {pr} - ({constant})'
            reason=f'You added {constant} on the right instead of subtracting it. Subtract {constant} from both sides to preserve equality.'
        rows[i].update(status='incorrect',reason=reason)
        for row in rows[i+1:]:row.update(status='dependent',reason='Depends on the earlier incorrect transformation; not labelled as a separate mistake.')
        result.update(status='incorrect_step_detected',first_incorrect_step=i+1,error_category=category,verified_correction=correction,message=reason)
        break
    else:result.update(status='correct',message='All submitted linear equations retain the original unique solution. Review the final answer below.')
    # Bounded targeted practice, checked independently by the same solver.
    practice=f'3{variable} + 5 = 20'
    checked=solve(practice,variable)
    result['practice']={'equation':practice,'variable':variable,'hint':'Subtract 5 from both sides, then divide both sides by 3.'} if checked['verified'] else None
    return result
