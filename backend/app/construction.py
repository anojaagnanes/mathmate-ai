"""Ruler-and-compass construction guides (English + Tamil).

Deterministic authored procedures for common school constructions. These are
standard instrument steps parameterized by the question's own numbers — not
solver algebra — so responses label them as procedures with on-drawing checks.
"""
import math
import re

EN_KEYS = ['construct', 'compass', 'straightedge', 'locus', 'equidistant',
           'tangent', 'bisect', 'perpendicular bisector']
TA_KEYS = ['அமை', 'கவராய', 'விளிம்பு', 'வட்ட', 'தொடலி', 'தொடு', 'தொட்',
           'சமதூர', 'ஒழுக்கு', 'முக்கோணி', 'செங்கோண', 'கோணம்', 'நடுக்குத்து']

ROMAN = {'i': 1, 'ii': 2, 'iii': 3, 'iv': 4, 'v': 5, 'vi': 6}


def _normalize(text):
    text = re.sub(r'([A-Z]{1,3})\s*-\s*(\d)', r'\1=\2', text)
    return text


def _fix_angle_ocr(value):
    # A degree sign misread as 3: 903 means 90 degrees in school geometry.
    if len(value) == 3 and value[2] == '3' and value[:2] in ('30', '45', '60', '90'):
        return value[:2]
    return value


def split_parts(text):
    """Split 'i. ... ii. ...' into labeled parts; whole text when unmarked."""
    lines = text.splitlines()
    parts, current, label = [], [], None
    for line in lines:
        m = re.match(r'\s*(i{1,3}|iv|v|vi)\s*[.)]\s*(.*)$', line, re.I)
        if m and len(m.group(1)) <= 3:
            if label is not None:
                parts.append((label, '\n'.join(current).strip()))
            label, current = m.group(1).lower(), [m.group(2)]
        elif label is not None:
            current.append(line)
    if label is not None:
        parts.append((label, '\n'.join(current).strip()))
        return [(label, part) for label, part in parts if part]
    return [('i', text.strip())]


def _measurements(part):
    part = _normalize(part)
    sides = {}
    for seg, val, unit in re.findall(r'([A-Z]{1,2})\s*=\s*(\d+(?:\.\d+)?)\s*(cm|mm)', part):
        sides[seg] = (val, unit)
    angles = {}
    for name, val in re.findall(r'([A-Z]{3})\s*=\s*(\d{2,3})\s*°?', part):
        angles[name] = _fix_angle_ocr(val)
    points = [p for p in re.findall(r'(?<![A-Za-z])[A-Z](?![A-Za-z])', part)]
    points = list(dict.fromkeys(points))
    return sides, angles, points


def _side_txt(seg, sides):
    return f'{seg} = {sides[seg][0]} {sides[seg][1]}' if seg in sides else f'side {seg}'


def _guide(label, kind, source, title_en, title_ta, given, steps, checks, diagram):
    return {'label': label, 'matched': True, 'kind': kind, 'source': source[:300],
            'title_en': title_en, 'title_ta': title_ta, 'given': given,
            'steps': steps, 'checks': checks, 'diagram': diagram}


def _triangle(label, part, sides, angles, points):
    if len(sides) < 1:
        return None
    segs = list(sides)
    a, b = segs[0], segs[1] if len(segs) > 1 else segs[0]
    common = ''.join(sorted(set(a) & set(b))) or b[0]
    other_a, other_b = (a.replace(common, '') or a[0]), (b.replace(common, '') or b[0])
    ang_name = next((k for k in angles if common in k), '')
    deg = angles.get(ang_name, '90')
    third = ''.join(p for p in (other_a, common, other_b))
    right = deg == '90'
    hypo = ''
    if right and len(sides) >= 2:
        try:
            hypo = f'{math.hypot(float(sides[a][0]), float(sides[b][0])):.1f}'
        except ValueError:
            hypo = ''
    given = ', '.join([_side_txt(s, sides) for s in segs] +
                      ([f'∠{ang_name} = {deg}°'] if ang_name else []))
    unit = next((u for _, u in sides.values()), 'cm')
    steps = [
        {'en': f'Draw a line and mark {_side_txt(b, sides)} on it. Call the ends {common} and {other_b}.',
         'ta': f'ஒரு கோடு வரைந்து அதில் {_side_txt(b, sides)} எனக் குறிக்கவும். முனைகளை {common}, {other_b} எனக் கொள்க.',
         'why_en': 'Every construction starts from a measured base — this fixes the first side exactly.',
         'why_ta': 'ஒவ்வொரு அமைப்பும் அளந்த அடிப்பக்கத்திலிருந்து தொடங்கும் — இது முதல் பக்கத்தைத் துல்லியமாக நிலைநிறுத்தும்.'},
        {'en': f'At {common}, construct the {deg}° angle' + (' with a perpendicular (ruler and compass arcs)' if right else ' with a protractor') + '.',
         'ta': f'{common}-யில் {deg}° கோணத்தை' + (' செங்குத்துக்கோடாக (நேர்விளிம்பு, கவராய விற்கள்) அமைக்கவும்.' if right else ' பாகைமானியால் அமைக்கவும்.'),
         'why_en': 'The included angle fixes the triangle\u2019s shape — without it the sides could swing anywhere.',
         'why_ta': 'உள்ளடக்கு கோணம்தான் முக்கோணியின் வடிவத்தை நிலைநிறுத்தும் — இல்லாவிடில் பக்கங்கள் எங்கும் சுழலும்.'},
        {'en': f'Measure {_side_txt(a, sides)} from {common} along the new line and mark {other_a}.',
         'ta': f'புதிய கோட்டில் {common}-யிலிருந்து {_side_txt(a, sides)} அளந்து {other_a}-ஐக் குறிக்கவும்.',
         'why_en': 'The graduated ruler gives the second side directly from the angle vertex.',
         'why_ta': 'அளவுள்ள நேர்விளிம்பு கோண உச்சியிலிருந்து இரண்டாம் பக்கத்தை நேரடியாகத் தரும்.'},
        {'en': f'Join {other_a} to {other_b} to close triangle {third}.',
         'ta': f'{other_a}-ஐ {other_b}-யுடன் இணைத்து {third} முக்கோணியை மூடுக.',
         'why_en': 'Two sides and their included angle determine exactly one triangle.',
         'why_ta': 'இரு பக்கங்களும் அவற்றின் உள்ளடக்கு கோணமும் சரியாக ஒரே முக்கோணியைத் தீர்மானிக்கும்.'},
    ]
    checks = [{'en': f'Measure all sides and the angle at {common} on your drawing.',
               'ta': f'உங்கள் வரைபடத்தில் எல்லாப் பக்கங்களையும் {common}-யிலுள்ள கோணத்தையும் அளக்கவும்.'}]
    if hypo:
        checks.append({'en': f'The third side should measure about {hypo} {unit}.',
                       'ta': f'மூன்றாம் பக்கம் ஏறத்தாழ {hypo} {unit} இருக்க வேண்டும்.'})
    return _guide(label, 'triangle', part, f'Construct triangle {third}', f'{third} முக்கோணி அமைத்தல்',
                  given, steps, checks,
                  {'kind': 'triangle', 'a': other_a, 'b': common, 'c': other_b,
                   'ab': sides.get(a, ('', ''))[0], 'bc': sides.get(b, ('', ''))[0],
                   'unit': unit, 'right': '1' if right else ''})


def _bisector(label, part, points):
    p1 = points[0] if len(points) > 0 else 'A'
    p2 = points[1] if len(points) > 1 else 'B'
    if p1 == p2:
        p2 = 'B' if p1 != 'B' else 'A'
    steps = [
        {'en': f'Join {p1} and {p2} with a straight line.',
         'ta': f'{p1}, {p2}-ஐ நேர்கோட்டால் இணைக்கவும்.',
         'why_en': 'The locus is defined relative to this segment — draw it first.',
         'why_ta': 'ஒழுக்கு இந்தத் துண்டை அடிப்படையாகக் கொண்டது — முதலில் அதை வரைக.'},
        {'en': f'With centre {p1} and radius more than half of {p1}{p2}, draw arcs above and below the line.',
         'ta': f'{p1}-ஐ மையமாகக் கொண்டு {p1}{p2}-யின் பாதிக்கு மேல் ஆரத்தில் கோட்டுக்கு மேலும் கீழும் விற்கள் வரைக.',
         'why_en': f'Equal radii from {p1} guarantee equal distance from {p1}.',
         'why_ta': f'{p1}-யிலிருந்து சம ஆரங்கள் சமதூரத்தை உறுதி செய்யும்.'},
        {'en': f'With the SAME radius and centre {p2}, draw arcs cutting the first pair. Mark the cuts P and Q.',
         'ta': f'அதே ஆரத்தில் {p2}-ஐ மையமாகக் கொண்டு முதல் விற்களை வெட்டும் விற்கள் வரைக; வெட்டுகளை P, Q எனக் குறிக்கவும்.',
         'why_en': f'The same radius from {p2} means P and Q are equally far from {p1} and {p2}.',
         'why_ta': f'{p2}-யிலிருந்தும் அதே ஆரம் என்பதால் P, Q இரண்டும் {p1}, {p2}-யிலிருந்து சமதூரத்தில் உள்ளன.'},
        {'en': 'Join P and Q with a straight line.',
         'ta': 'P, Q-ஐ நேர்கோட்டால் இணைக்கவும்.',
         'why_en': f'Line PQ is the perpendicular bisector — EVERY point on it is equidistant from {p1} and {p2}. This line IS the locus.',
         'why_ta': f'PQ கோடுதான் நடுக்குத்துக்கோடு — இதிலுள்ள ஒவ்வொரு புள்ளியும் {p1}, {p2}-யிலிருந்து சமதூரத்தில் இருக்கும். இந்தக் கோடே ஒழுக்கு.'},
    ]
    checks = [{'en': f'Pick any point on PQ and measure to {p1} and {p2} — both equal; PQ meets {p1}{p2} at 90° at its midpoint.',
               'ta': f'PQ-யில் ஏதேனும் ஒரு புள்ளியை எடுத்து {p1}, {p2}-க்கு அளக்கவும் — இரண்டும் சமம்; PQ, {p1}{p2}-ஐ நடுப்புள்ளியில் 90°-யில் வெட்டும்.'}]
    return _guide(label, 'perp_bisector', part,
                  f'Locus of points equidistant from {p1} and {p2}',
                  f'{p1}, {p2}-யிலிருந்து சமதூரப் புள்ளிகளின் ஒழுக்கு',
                  f'Points {p1}, {p2}', steps, checks,
                  {'kind': 'perp_bisector', 'p1': p1, 'p2': p2})


def _tangent_circle(label, part):
    at = re.search(r'([A-Z])\s*(?:இல்|\bat\b)', part)
    at = at.group(1) if at else 'B'
    thru = re.search(r'([A-Z])\s*(?:இனூடாக|வழியாக|வழி|through|passes)', part)
    thru = thru.group(1) if thru else ('A' if at != 'A' else 'C')
    line = re.search(r'([A-Z]{2})', part)
    line = line.group(1) if line else at + 'C'
    steps = [
        {'en': f'Draw line {line} and mark point {at} on it; mark point {thru} off the line.',
         'ta': f'{line} கோட்டை வரைந்து அதில் {at}-ஐயும் கோட்டுக்கு வெளியே {thru}-ஐயும் குறிக்கவும்.',
         'why_en': f'The tangent touches at exactly one point {at}; the circle must also carry {thru}.',
         'why_ta': f'தொடலி {at} என்ற ஒரே புள்ளியில் தொடும்; வட்டம் {thru}-ஐயும் கொண்டிருக்க வேண்டும்.'},
        {'en': f'At {at}, erect a perpendicular to {line}.',
         'ta': f'{at}-யில் {line}-க்குச் செங்குத்துக்கோடு எழுப்புக.',
         'why_en': 'A circle\u2019s centre always lies on the perpendicular to a tangent at the touch point.',
         'why_ta': 'வட்ட மையம் எப்போதும் தொடுபுள்ளியில் தொடலிக்குச் செங்குத்தான கோட்டில்தான் இருக்கும்.'},
        {'en': f'Join {at} and {thru}; construct the perpendicular bisector of {at}{thru} (arcs from each end, join the cuts).',
         'ta': f'{at}, {thru}-ஐ இணைக்கவும்; {at}{thru}-யின் நடுக்குத்துக்கோட்டை அமைக்கவும் (இரு முனையிலிருந்தும் விற்கள், வெட்டுகளை இணைக்கவும்).',
         'why_en': f'Every point on this bisector is equally far from {at} and {thru} — the centre must be one of them.',
         'why_ta': f'இந்தக் கோட்டிலுள்ள ஒவ்வொரு புள்ளியும் {at}, {thru}-யிலிருந்து சமதூரம் — மையமும் இதில் இருக்க வேண்டும்.'},
        {'en': 'Mark where the two lines meet as O — this is the centre.',
         'ta': 'இரு கோடுகளும் சந்திக்குமிடத்தை O எனக் குறிக்கவும் — இதுவே மையம்.',
         'why_en': 'O satisfies both conditions at once, so it is the unique centre.',
         'why_ta': 'O இரு நிபந்தனைகளையும் ஒரே நேரத்தில் நிறைவு செய்வதால் இதுவே ஒரே மையம்.'},
        {'en': f'With centre O and radius O{at}, draw the circle.',
         'ta': f'O-ஐ மையமாகவும் O{at}-ஐ ஆரமாகவும் கொண்டு வட்டம் வரைக.',
         'why_en': f'Radius O{at} touches {line} exactly at {at}, and the circle passes through {thru}.',
         'why_ta': f'O{at} ஆரம் {line}-ஐ {at}-யில் மட்டும் தொடும்; வட்டம் {thru} வழியாகச் செல்லும்.'},
    ]
    checks = [{'en': f'Measure O{at} = O{thru}; confirm the circle touches {line} only at {at}.',
               'ta': f'O{at} = O{thru} என அளக்கவும்; வட்டம் {line}-ஐ {at}-யில் மட்டும் தொடுவதை உறுதி செய்க.'}]
    return _guide(label, 'tangent_circle', part,
                  f'Circle touching {line} at {at}, through {thru}',
                  f'{at}-யில் {line}-ஐத் தொட்டு {thru} வழிச் செல்லும் வட்டம்',
                  f'Tangent point {at}, through {thru}', steps, checks,
                  {'kind': 'tangent_circle', 'at': at, 'thru': thru, 'line': line})


def _external_tangent(label, part):
    frm = re.search(r'([A-Z])\s*(?:இலிருந்து|\bfrom\b)', part)
    frm = frm.group(1) if frm else 'C'
    exc = re.search(r'([A-Z]{2})\s*(?:தவிர்ந்த|except|other than|besides)', part)
    exc = exc.group(1) if exc else ''
    steps = [
        {'en': f'Join the circle\u2019s centre O to the outside point {frm}.',
         'ta': f'வட்ட மையம் O-ஐ வெளிப்புள்ளி {frm}-யுடன் இணைக்கவும்.',
         'why_en': 'The new touch point lies on the circle with O{frm} as diameter.'.format(frm=frm),
         'why_ta': f'புதிய தொடுபுள்ளி O{frm}-ஐ விட்டமாகக் கொண்ட வட்டத்தில் இருக்கும்.'},
        {'en': f'Bisect O{frm} to find its midpoint M.',
         'ta': f'O{frm}-ஐ இருசமப்படுத்தி நடுப்புள்ளி M-ஐக் காண்க.',
         'why_en': 'M is the centre of the helper circle.',
         'why_ta': 'M துணை வட்டத்தின் மையம்.'},
        {'en': 'With centre M and radius MO, draw a circle cutting the given circle at T.',
         'ta': 'M-ஐ மையமாகவும் MO-ஐ ஆரமாகவும் கொண்டு கொடுத்த வட்டத்தை T-யில் வெட்டும் வட்டம் வரைக.',
         'why_en': f'Angle OT{frm} is 90° (angle in a semicircle), so {frm}T touches the circle exactly at T.',
         'why_ta': f'OT{frm} கோணம் 90° (அரைவட்டக் கோணம்), எனவே {frm}T வட்டத்தை T-யில் மட்டும் தொடும்.'},
        {'en': f'Join {frm} to T — this is the required tangent' + (f' (the other one is {exc})' if exc else '') + '.',
         'ta': f'{frm}-ஐ T-யுடன் இணைக்கவும் — இதுவே தேவையான தொடலி' + (f' (மற்றது {exc})' if exc else '') + '.',
         'why_en': 'CT meets radius OT at 90° — the tangent condition.'.replace('CT', f'{frm}T'),
         'why_ta': f'{frm}T, OT ஆரத்தை 90°-யில் சந்திக்கிறது — இதுவே தொடலி நிபந்தனை.'},
    ]
    checks = [{'en': f'Angle OT{frm} = 90°; {frm}T touches the circle only at T.',
               'ta': f'OT{frm} கோணம் = 90°; {frm}T வட்டத்தை T-யில் மட்டும் தொடும்.'}]
    return _guide(label, 'external_tangent', part,
                  f'Tangent from {frm} to the circle',
                  f'{frm}-யிலிருந்து வட்டத்திற்குத் தொடலி',
                  f'From {frm}' + (f', other than {exc}' if exc else ''), steps, checks,
                  {'kind': 'external_tangent', 'from': frm, 'given': exc})


def _is_tangent_text(part):
    low = part.lower()
    return ('tangent' in low or 'touch' in low or 'தொடலி' in part or 'தொடு' in part
            or 'தொட்' in part or 'தொட்ட' in part)


def _match_part(label, part):
    low = part.lower()
    has_circle = 'circle' in low or 'வட்ட' in part
    if _is_tangent_text(part) and has_circle and ('from' in low or 'இலிருந்து' in part or 'மற்றைய' in part or 'other' in low or 'except' in low or 'தவிர்ந்த' in part):
        return _external_tangent(label, part)
    if _is_tangent_text(part) and has_circle and ('through' in low or 'passes' in low or 'இனூடாக' in part or 'வழி' in part or 'செல்' in part):
        return _tangent_circle(label, part)
    if 'equidistant' in low or 'சமதூர' in part or 'locus' in low or 'ஒழுக்கு' in part:
        _, _, points = _measurements(part)
        return _bisector(label, part, points)
    if 'triangle' in low or 'முக்கோணி' in part:
        sides, angles, points = _measurements(part)
        guide = _triangle(label, part, sides, angles, points)
        if guide:
            return guide
    return None


def match_constructions(text):
    """Return construction guides for multi-part construction text, else None."""
    low = text.lower()
    if not any(k in low for k in EN_KEYS) and not any(k in text for k in TA_KEYS):
        return None
    guides = []
    for label, part in split_parts(text):
        if not part or len(part) > 1200:
            continue
        guide = _match_part(label, part)
        if guide:
            guides.append(guide)
    return guides or None
