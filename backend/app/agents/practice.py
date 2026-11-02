"""Cost-free, bounded fraction practice; every answer computed exactly by SymPy."""
import sympy as sp
from pydantic import BaseModel

class PracticeSpec(BaseModel):
    equation: str
    variable: str | None = None
    hint: str
    topic: str = 'fractions'
    difficulty: int
    answer: str
    kind: str = 'value'

class PracticeAgent:
    async def generate_with_provider(self,provider,category='addition',history=(),seen=()):
        fallback=self.generate(category,history,seen)
        if not fallback:return None
        if not hasattr(provider,'draft_practice'):return fallback
        try:
            draft=await provider.draft_practice(category,fallback['difficulty'],seen)
            n,d,m,e=draft.numerator_a,draft.denominator_a,draft.numerator_b,draft.denominator_b
            level=fallback['difficulty']
            if level==0 and d!=e:raise ValueError('Difficulty mismatch')
            if level==1 and d%e!=0 and e%d!=0:raise ValueError('Difficulty mismatch')
            if level==2 and d==e:raise ValueError('Difficulty mismatch')
            a,b=sp.Rational(n,d),sp.Rational(m,e)
            if category=='comparison':
                question=f'Compare {n}/{d} and {m}/{e} (enter <, = or >)';answer='<' if a<b else '>' if a>b else '=';kind='comparison'
            elif category=='equivalence':
                question=f'{n}/{d}';answer=str(a);kind='value'
            else:question=f'{n}/{d} + {m}/{e}';answer=str(a+b);kind='value'
            if question in seen:raise ValueError('Duplicate practice')
            return dict(fallback,equation=question,answer=answer,kind=kind)
        except Exception:
            return dict(fallback)

    def generate(self, category='addition', history=(), seen=()):
        recent=list(history)[-3:]
        level=2 if len(recent)==3 and all(r['correct'] for r in recent) else 1 if recent and recent[-1]['correct'] else 0
        for offset in range(30):
            d=3+offset; a=sp.Rational(1,d); b=sp.Rational(1,d if level==0 else 2*d if level==1 else d+1)
            if category=='comparison':
                question=f'Compare 1/{d} and 2/{d+2} (enter <, = or >)'
                value=sp.Rational(2,d+2); answer='<' if a<value else '>' if a>value else '='
                kind='comparison';hint='Use a common denominator, then compare the numerators.'
            elif category=='equivalence':
                question=f'{2}/{2*d}'
                answer=str(a);kind='value';hint='Divide numerator and denominator by their common factor.'
            else:
                question=f'1/{d} + {b.p}/{b.q}'
                answer=str(a+b);kind='value';hint='Rewrite both fractions with a common denominator, then add the numerators.'
            if question not in seen:
                return PracticeSpec(equation=question,hint=hint,difficulty=level,answer=answer,kind=kind).model_dump()
        return None

    def public(self,question):
        return {k:v for k,v in question.items() if k!='answer'} if question else None
