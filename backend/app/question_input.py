"""Conservative English and Tamil interpretation. Full-sentence matches require user review."""
import re
from fractions import Fraction
from .math_parser import VARIABLES
from .topic_maths import COMMANDS
from .construction import match_constructions

MATH_NAMES = VARIABLES | frozenset('sqrt sin cos tan log exp pi E diff integrate Matrix Vector det inverse transpose matmul matrixadd dot cross norm d dx dy dz dn da db dc dt du dv dtheta dalpha dbeta'.split())
MATH_NAMES |= COMMANDS

TAMIL_DIGITS = {'\u0be6': '0', '\u0be7': '1', '\u0be8': '2', '\u0be9': '3', '\u0bea': '4', '\u0beb': '5', '\u0bec': '6', '\u0bed': '7', '\u0bee': '8', '\u0bef': '9'}


def normalize_tamil_digits(text):
    for ta, en in TAMIL_DIGITS.items():
        text = text.replace(ta, en)
    return text


def has_tamil_script(text: str) -> bool:
    return any('\u0b80' <= ch <= '\u0bff' for ch in text)


def needs_interpretation(text: str) -> bool:
    # A conservative lexical gate, not a natural-language solver. Unknown words
    # never get stripped away to leave an unrelated, apparently verified equation.
    normalized = normalize_tamil_digits(text)
    names = re.findall(r'[^\W\d]+', normalized.replace('\u03c0', 'pi').replace('\u00b2', '').replace('\u00b3', ''), re.UNICODE)
    return '?' in text or any(name not in MATH_NAMES and name != 'e' for name in names)


def extract_math_fragment(text: str) -> str | None:
    """Find one explicit equation inside prose for tap-to-fill assistance.

    This is input help, not interpretation: the fragment is never executed
    here. The student must explicitly resubmit it as pure maths, which then
    travels the normal verified solver route on its own.
    """
    normalized = normalize_tamil_digits(text)
    for match in re.finditer(r'[0-9][0-9a-z+\-*/^(). ]{0,60}=[0-9a-z+\-*/^(). ]{1,60}', normalized, re.I):
        candidate = re.sub(r'\s+', '', match.group(0)).strip()
        if candidate and len(candidate) <= 200 and not needs_interpretation(candidate):
            return candidate
    return None


def _half_exact(value: str) -> str:
    """Halve a decimal/integer string exactly for diameter-to-radius."""
    d = Fraction(value)
    r = d / 2
    if r.denominator == 1:
        return str(r.numerator)
    return f'{r.numerator}/{r.denominator}'


def _parse_number_list(raw: str) -> list[str] | None:
    """Parse '2, 4, 6 and 8' into ['2','4','6','8']. Returns None if invalid."""
    cleaned = re.sub(r'\s+and\s+', ',', raw, flags=re.I)
    parts = [p.strip() for p in cleaned.split(',')]
    parts = [p for p in parts if p]
    if not 1 <= len(parts) <= 30:
        return None
    for p in parts:
        if not re.fullmatch(r'-?\d{1,5}(?:\.\d{1,4})?', p):
            return None
    return parts


def interpret_question(text: str) -> dict:
    cleaned = re.sub(r'\s+', ' ', text.strip()).rstrip('.?').strip()
    normalized = normalize_tamil_digits(cleaned)

    def match(pattern):
        return re.fullmatch(pattern, cleaned, re.I)

    def match_normalized(pattern):
        return re.fullmatch(pattern, normalized)

    def proposal(math, *assumptions, question_type=None):
        out = {'route': 'interpretation', 'status': 'review_required', 'question': text,
               'proposed_math': math, 'assumptions': list(assumptions),
               'message': 'Review the mathematical model below. Confirm that it represents your question before solving. It uses built-in rules; Mia will verify the confirmed model.'}
        if question_type:
            out['question_type'] = question_type
        return out

    number = r'\d{1,5}(?:\.\d{1,4})?'
    equivalent = match(r'why is (\d{1,4}/[1-9]\d{0,3}) (?:equal to|equivalent to) (\d{1,4}/[1-9]\d{0,3})')
    if equivalent:
        return proposal(f'{equivalent[1]} - {equivalent[2]}',
                        'Compare the two exact fractions by subtracting: zero means they are equivalent; a nonzero value means they are not. No equivalence is assumed.',
                        question_type='Fractions · Equivalence')
    sequence = re.fullmatch(r'\s*(T_?n)\s*=\s*([0-9n+\-*/^().\s]+)\s*', text)
    if sequence:
        term, expression = sequence[1], sequence[2].strip()
    else:
        sequence = re.fullmatch(r'\s*([0-9n+\-*/^().\s]+)\s*=\s*(T_?n)\s*', text)
        term, expression = (sequence[2], sequence[1].strip()) if sequence else ('', '')
    if sequence and 'n' in expression and len(expression) <= 190:
        result = proposal(expression + '=t',
                          f'Interpret {term} as the nth term value and represent it by t, not multiplication.',
                          'Solve for n in terms of t. No numerical term value has been supplied.',
                          'For a sequence position, any numerical n must also satisfy the sequence\u2019s allowed integer index range.',
                          question_type='Sequences · Formula')
        result['suggested_variable'] = 'n'
        result['message'] = 'This is a sequence formula. Review the notation: t represents the nth term value. Supply that value for a numerical position, or confirm to rearrange symbolically for n.'
        return result

    # Tamil geometry: circle area / circumference by radius.
    m = match_normalized(r'ஆரம்\s*(' + number + r')\s*உள்ள\s*வட்டத்தின்\s*பரப்பளவு\s*காண்க')
    if m:
        return proposal(f'circle_area({m[1]})', f'ஆரம் {m[1]} எனக் கொள்ளப்படுகிறது; விட்டம் அல்ல. அலகு குறிப்பிடப்படவில்லை எனில் பரப்பளவு சதுர அலகுகளில்.',
                        question_type='Geometry · Circle area')
    m = match_normalized(r'ஆரம்\s*(' + number + r')\s*உள்ள\s*வட்டத்தின்\s*சுற்றளவு\s*காண்க')
    if m:
        return proposal(f'circumference({m[1]})', f'ஆரம் {m[1]} எனக் கொள்ளப்படுகிறது; விட்டம் அல்ல.',
                        question_type='Geometry · Circle circumference')
    # Tamil diameter -> radius.
    m = match_normalized(r'விட்டம்\s*(' + number + r')\s*உள்ள\s*வட்டத்தின்\s*பரப்பளவு\s*காண்க')
    if m:
        try:
            radius = _half_exact(m[1])
        except Exception:
            radius = None
        if radius:
            return proposal(f'circle_area({radius})', f'விட்டம் {m[1]} என்பதால் ஆரம் {radius} (விட்டத்தில் பாதி).',
                            question_type='Geometry · Circle area')
    # Tamil rectangle / triangle.
    m = match_normalized(r'நீளம்\s*(' + number + r')\s*அகலம்\s*(' + number + r')\s*உள்ள\s*செவ்வகத்தின்\s*பரப்பளவு\s*காண்க')
    if m:
        return proposal(f'rectangle_area({m[1]},{m[2]})', f'நீளம் {m[1]}, அகலம் {m[2]}; இரண்டும் ஒரே அலகில். பரப்பளவு சதுர அலகுகளில்.',
                        question_type='Geometry · Rectangle area')
    m = match_normalized(r'அடிப்பக்கம்\s*(' + number + r')\s*உயரம்\s*(' + number + r')\s*உள்ள\s*முக்கோணத்தின்\s*பரப்பளவு\s*காண்க')
    if m:
        return proposal(f'triangle_area({m[1]},{m[2]})', f'அடிப்பக்கம் {m[1]}, செங்குத்து உயரம் {m[2]}. உயரம் சாய்வுப் பக்கம் அல்ல.',
                        question_type='Geometry · Triangle area')
    # Tamil calculate: கணக்கிடுக: <pure maths>
    m = match_normalized(r'கணக்கிடுக\s*:\s*(.+)')
    if m and len(m[1].strip()) <= 200 and not needs_interpretation(m[1].strip()):
        return proposal(re.sub(r'\s+', '', m[1].strip()), 'கொடுக்கப்பட்ட கோவையை மட்டும் மதிப்பிடுக; கூடுதல் அளவுகள் ஊகிக்கப்படவில்லை.',
                        question_type='Arithmetic · Evaluate')
    # Tamil solve: <math> (ஐ) தீர்க்கவும்
    m = match_normalized(r'(.+?)\s*(?:ஐ\s*)?தீர்க்கவும்\s*')
    if m:
        candidate = re.sub(r'\s+', '', m[1].strip())
        if candidate and len(candidate) <= 200 and not needs_interpretation(candidate):
            return proposal(candidate, 'காட்டப்பட்ட முழு கணிதக் கூற்றையும் மெய் எண்களில் தீர்க்கவும்.',
                            question_type='Equation · From sentence')

    # English: please solve ... for me.
    m = match(r'please solve (.+?)(?: for me)?')
    if m:
        candidate = re.sub(r'\s+', '', m[1].strip())
        if candidate and len(candidate) <= 200 and not needs_interpretation(candidate):
            return proposal(candidate, 'Solve the complete mathematical statement shown over the real numbers.',
                            question_type='Equation · From sentence')
    m = match(r'(?:what is|calculate|evaluate) (.+)')
    if m and len(m[1]) <= 200 and not needs_interpretation(m[1]):
        return proposal(m[1], 'Evaluate exactly the expression shown; no unstated quantities are inferred.',
                        question_type='Arithmetic · Evaluate')
    m = match(r'solve (.+)')
    if m and len(m[1]) <= 200 and not needs_interpretation(m[1]):
        return proposal(re.sub(r'\s+', '', m[1].strip()), 'Solve the complete mathematical statement shown over the real numbers.',
                        question_type='Equation · From sentence')
    m = match(r'(twice|three times) a number (plus|minus) (' + number + r') (?:is|equals) (' + number + r')')
    if m:
        factor = 2 if m[1].lower() == 'twice' else 3
        sign = '+' if m[2].lower() == 'plus' else '-'
        return proposal(f'{factor}*x{sign}{m[3]}={m[4]}', 'Let x represent the unknown number. Multiplication applies before addition/subtraction.',
                        question_type='Equation · Word problem')
    m = match(r'(?P<person>[A-Za-z]{1,30}) has (?P<initial>\d{1,5}) (?P<item>[A-Za-z]{1,30}) and (?P<action>buys|gets|receives|loses|gives away) (?P<change>\d{1,5})(?: more)?\. How many (?P=item) does (?:he|she|(?P=person)) have(?: now)?')
    if m:
        sign = '-' if m['action'].lower() in {'loses', 'gives away'} else '+'
        if sign == '-' and int(m['change']) > int(m['initial']):
            return {'route': 'interpretation', 'status': 'unsupported', 'question': text,
                    'message': 'The amount removed exceeds the starting count. Please clarify the quantities; no answer was inferred.'}
        return proposal(f"{m['initial']}{sign}{m['change']}", f"Count {m['item']}; the stated change is the only change to {m['person']}'s collection.",
                        question_type='Arithmetic · Word problem')
    # English geometry with diameter.
    m = match(r'(?:find|calculate) the area of a circle with diameter (' + number + r')\s*(cm|mm|m|km)?')
    if m:
        try:
            radius = _half_exact(m[1])
        except Exception:
            radius = None
        if radius:
            return proposal(f'circle_area({radius})', f'Diameter {m[1]} {m[2] or ""} gives radius {radius} (half the diameter).'.strip(),
                            question_type='Geometry · Circle area')
    m = match(r'find the hypotenuse of a right triangle with legs (' + number + r') and (' + number + r')\s*(cm|mm|m|km)?')
    if m:
        return proposal(f'hypotenuse({m[1]},{m[2]})', f'Legs {m[1]} and {m[2]} are perpendicular; both use {m[3] or "the same unspecified unit"}.',
                        question_type='Geometry · Right-triangle hypotenuse')
    m = match(r'(?:find|calculate) the area of a square with side (' + number + r')\s*(cm|mm|m|km)?')
    if m:
        return proposal(f'rectangle_area({m[1]},{m[1]})', f'A square with side {m[1]} {m[2] or ""} is a rectangle with equal sides; area is in squared units.'.strip(),
                        question_type='Geometry · Square area')
    m = match(r'(?:find|calculate) the (area|perimeter) of a rectangle with length (' + number + r')\s*(cm|mm|m|km)? and width (' + number + r')\s*(cm|mm|m|km)?')
    if m and (m[3] or '').lower() == (m[5] or '').lower():
        kind = 'area' if m[1].lower() == 'area' else 'perimeter'
        return proposal(f'rectangle_{kind}({m[2]},{m[4]})', f'Length and width use {m[3] or "the same unspecified unit"}. Area is in squared units; perimeter is in length units.',
                        question_type=f'Geometry · Rectangle {kind}')
    m = match(r'(?:find|calculate) the area of a triangle with base (' + number + r')\s*(cm|mm|m|km)? and (?:perpendicular )?height (' + number + r')\s*(cm|mm|m|km)?')
    if m and (m[2] or '').lower() == (m[4] or '').lower():
        return proposal(f'triangle_area({m[1]},{m[3]})', f'Height is perpendicular to the base. Both lengths use {m[2] or "the same unspecified unit"}; the answer uses squared units.',
                        question_type='Geometry · Triangle area')
    m = match(r'(?:find|calculate) the (area|circumference) of a circle with radius (' + number + r')\s*(cm|mm|m|km)?')
    if m:
        kind = 'area' if m[1].lower() == 'area' else 'circumference'
        return proposal(f'{"circle_area" if kind == "area" else "circumference"}({m[2]})', f'The supplied value is the radius, not diameter, in {m[3] or "unspecified length units"}.',
                        question_type=f'Geometry · Circle {kind}')
    # Statistics: mean of list.
    m = match(r'(?:find|calculate) the mean of (.+)')
    if m:
        values = _parse_number_list(m[1])
        if values:
            return proposal(f'mean([{",".join(values)}])', f'Mean of {len(values)} values; each listed value counts as one observation.',
                            question_type='Statistics · Mean')
    # Counting: choose k from n.
    m = match(r'how many ways to choose (\d{1,3}) from (\d{1,3})')
    if m:
        k, n = int(m[1]), int(m[2])
        if 0 <= k <= n <= 100:
            return proposal(f'choose({n},{k})', f'Choose {k} of {n} distinct objects without replacement; order does not matter.',
                            question_type='Counting · Combinations')
    # Probability.
    m = match(r'(?:find|calculate) the probability of (\d{1,3}) favorable out of (\d{1,3})')
    if m:
        fav, total = int(m[1]), int(m[2])
        if 0 <= fav <= total and total > 0 and total <= 100:
            return proposal(f'probability({fav},{total})', f'Assuming {total} equally likely outcomes with {fav} favorable.',
                            question_type='Probability')

    guides = match_constructions(text)
    if guides:
        tamil = has_tamil_script(text)
        return {'route': 'construction', 'status': 'solved', 'question': text,
                'question_type': 'Geometry · Constructions', 'guides': guides,
                'message': ('அமைப்பு வழிகாட்டிகள் தயார் — ஒவ்வொரு பகுதியையும் படிப்படியாகப் பாருங்கள். இவை நிலையான கருவி-முறை படிகள்; உங்கள் வரைபடத்தில் அளவுகளைச் சரிபார்க்கவும்.'
                            if tamil else
                            'Construction guides ready — work through each part step by step. These are standard instrument procedures; verify measurements on your drawing.')}
    fragment = extract_math_fragment(text)
    if has_tamil_script(text):
        message = 'இந்த தமிழ் விளக்கத்தை நேரடியாகத் தீர்க்க முடியவில்லை. எண்களையும் சமன்பாட்டையும் தட்டச்சு செய்யுங்கள் (எ.கா. 2x+3=11). No answer was inferred.'
        if fragment:
            message += f' நீங்கள் {fragment} என்ற சமன்பாட்டை நினைத்தால், அதைத் தட்டச்சு செய்து Solve அழுத்துங்கள்.'
        return {'route': 'interpretation', 'status': 'unsupported', 'message': message,
                'question': text, 'suggested_input': fragment}
    message = 'This wording is outside the supported English interpretation rules. No answer has been inferred. Try a supported example, enter the mathematical model directly, or clarify the quantities. Mixed units and image-only diagrams need manual interpretation.'
    if fragment:
        message += f' If you meant the equation {fragment}, enter it alone and press Solve.'
    return {'route': 'interpretation', 'status': 'unsupported', 'message': message,
            'question': text, 'suggested_input': fragment}
