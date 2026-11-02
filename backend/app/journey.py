"""Learning Journey: an autonomous five-stage practice path.

One journey, five stages, continuous questions. The agent plans the route
from the student's persisted history (the final stage focuses on the
weakest topic), ramps each stage easy -> medium -> advanced, and keeps the
questions flowing: correct answers build progress, wrong answers retry the
same question (taught after 3 misses), and three help options (hint, guiding
step, full solution)
catch stuck students without ever stopping the journey. Every question and
help step is produced by the deterministic engines; the agent never grades
by prose.
"""
import copy
import math
import re
import secrets
import time
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from .math_parser import MathError
from .math_runtime import solve, expression, answer_value
from .models import Journey, User
from .missions import diagnose, generate_linear_drill, generate_spot_drill, grade_spot, recent_drill_equations
from .agents.practice import PracticeAgent

GEMS_NEEDED = 3
MAX_PER_ISLAND = 8
MAX_MISSES = 3

ISLAND_DEFS = [
    {'key': 'driftwood', 'title': 'Linear equations', 'subtitle': 'Stage 1 of 5 · gentle start',
     'topic': 'equations', 'kind': 'linear'},
    {'key': 'shallows', 'title': 'Adding fractions', 'subtitle': 'Stage 2 of 5 · building up',
     'topic': 'fractions', 'kind': 'addition'},
    {'key': 'peaks', 'title': 'X-intercepts', 'subtitle': 'Stage 3 of 5 · graphs',
     'topic': 'graphs', 'kind': 'graph'},
    {'key': 'lagoon', 'title': 'Equivalent fractions', 'subtitle': 'Stage 4 of 5 · deeper practice',
     'topic': 'fractions', 'kind': 'lagoon'},
    {'key': 'cove', 'title': 'Mixed challenge', 'subtitle': 'Stage 5 of 5 · your weakest area',
     'topic': 'boss', 'kind': 'boss'},
]


def generate_graph_drill(difficulty, seen):
    """X-intercept drills in the quiz shape, verified by the solver."""
    for _ in range(50):
        level = min(3, max(1, difficulty))
        answer = secrets.randbelow(13) - 6
        a = secrets.randbelow(3 * level) + 1
        equation = f'{a}x + ({-a * answer}) = 0'
        if equation in seen:
            continue
        try:
            result = solve(equation)
        except MathError:
            continue
        if result.get('verified') and result.get('kind') == 'unique':
            steps = result.get('steps', [])
            return {'equation': equation, 'answer': result['solution'], 'kind': 'value',
                    'difficulty': level, 'hint': steps[1]['explanation'] if len(steps) > 1 else 'Set y = 0, then isolate x by reversing each operation.'}
    raise MathError('Could not generate a verified drill. Please try again.')


def _practice_drill(category, seen, history):
    question = PracticeAgent().generate(category, history, seen)
    if question is None and seen:
        question = PracticeAgent().generate(category, history, ())
    if question is None:
        return None
    return {'equation': question['equation'], 'answer': question['answer'], 'kind': question['kind'],
            'difficulty': question.get('difficulty', 1) + 1, 'hint': question['hint']}


def generate_island_drill(island, difficulty, seen, history):
    """Serve the island's question type; fall back to linear rather than stall."""
    kind = island['kind']
    if kind == 'linear':
        return generate_linear_drill(difficulty, seen)
    if kind == 'graph':
        return generate_graph_drill(difficulty, seen)
    if kind == 'lagoon':
        category = 'equivalence' if island.get('asked', 0) % 2 == 0 else 'comparison'
        drill = _practice_drill(category, seen, history)
        if drill:
            return drill
        return generate_linear_drill(difficulty, seen)
    if kind == 'boss':
        if island.get('boss_fractions'):
            category = 'addition' if island.get('asked', 0) % 2 == 0 else 'equivalence'
            drill = _practice_drill(category, seen, history)
            if drill:
                return drill
        return generate_linear_drill(difficulty, seen)
    drill = _practice_drill('addition', seen, history)
    if drill:
        return drill
    return generate_linear_drill(difficulty, seen)


def guardian_spot(island, seen, history):
    """The boss island's guardian: one role-reversal round, or None."""
    if island['kind'] != 'boss':
        return None
    if any(entry.get('kind') == 'spot_mistake' for entry in history):
        return None
    if island.get('gems', 0) < 2:
        return None
    try:
        if island.get('boss_fractions'):
            return generate_spot_drill('fractions', 'addition', island.get('difficulty', 2), seen, history)
        return generate_spot_drill('equations', 'linear', island.get('difficulty', 2), seen, history)
    except MathError:
        return None


def _fraction_terms(equation):
    parts = [p.strip() for p in equation.split('+')]
    if len(parts) != 2:
        return None
    try:
        left = expression(parts[0])
        right = expression(parts[1])
    except MathError:
        return None
    if left.q == 1 and right.q == 1:
        return None
    return int(left.p), int(left.q), int(right.p), int(right.q)


def guiding_nudge(drill):
    """One engine-derived guiding step. Never the final answer, never a guess."""
    try:
        if drill.get('kind') == 'spot_mistake':
            return {'text': "Work backwards: check Mia's last line against the line above it and verify its value first.",
                    'step': None}
        if drill.get('kind') == 'comparison':
            match = re.findall(r'(\d+)\s*/\s*(\d+)', drill.get('equation', ''))
            if len(match) >= 2:
                (a, b), (c, d) = (int(x) for x in match[0]), (int(x) for x in match[1])
                common = math.lcm(b, d)
                return {'text': f'Rewrite both with denominator {common}, then compare the tops — but decide <, = or > yourself.',
                        'step': {'equation': f'{a * common // b}/{common} ? {c * common // d}/{common}',
                                 'explanation': f'Multiply to reach the common denominator {common}.'}}
            raise MathError('unparseable')
        terms = _fraction_terms(drill.get('equation', ''))
        if terms:
            a, b, c, d = terms
            common = math.lcm(b, d)
            return {'text': f'Rewrite both fractions with denominator {common}, then add the tops.',
                    'step': {'equation': f'{a * common // b}/{common} + {c * common // d}/{common}',
                             'explanation': f'Multiply each fraction to reach the common denominator {common}.'}}
        if '/' in drill.get('equation', '') and '=' not in drill.get('equation', ''):
            value = expression(drill['equation'])
            if value.q != 1:
                g = math.gcd(int(value.p), int(value.q))
                if g > 1:
                    return {'text': f'Divide the top and bottom by {g}, then enter the simplest form.',
                            'step': {'equation': f'{int(value.p) // g}/{int(value.q) // g}',
                                     'explanation': f'{g} divides both {value.p} and {value.q}.'}}
            return {'text': 'That fraction is already in simplest form — enter it as it is.', 'step': None}
        result = solve(drill['equation'])
        steps = result.get('steps', [])
        if len(steps) > 1:
            return {'text': 'Mia shows just the next step — finish it yourself.',
                    'step': {'equation': steps[1].get('equation', ''), 'explanation': steps[1].get('explanation', '')}}
        if steps:
            return {'text': 'Mia shows just the next step — finish it yourself.',
                    'step': {'equation': steps[0].get('equation', ''), 'explanation': steps[0].get('explanation', '')}}
    except MathError:
        pass
    return {'text': 'Re-read the hint above: undo one operation at a time, keeping both sides balanced.', 'step': None}


def reveal_solution(drill):
    """The full verified solution. Using it marks the question assisted: no gem."""
    try:
        if drill.get('kind') == 'spot_mistake':
            return {'text': drill.get('explanation') or 'Study which line loses the verified solution.',
                    'steps': [{'equation': s, 'explanation': ''} for s in drill.get('steps') or []],
                    'answer': f"line {drill.get('wrong_line', '')}"}
        if drill.get('kind') == 'comparison':
            match = re.findall(r'(\d+)\s*/\s*(\d+)', drill.get('equation', ''))
            steps = []
            if len(match) >= 2:
                (a, b), (c, d) = (int(x) for x in match[0]), (int(x) for x in match[1])
                common = math.lcm(b, d)
                left, right = a * common // b, c * common // d
                steps = [{'equation': f'{left}/{common} vs {right}/{common}',
                          'explanation': f'Common denominator {common}: compare {left} and {right}.'}]
            return {'text': f"The verified answer is {drill['answer']}.", 'steps': steps, 'answer': drill['answer']}
        terms = _fraction_terms(drill.get('equation', ''))
        if terms:
            a, b, c, d = terms
            common = math.lcm(b, d)
            total = expression(drill['equation'])
            steps = [{'equation': f'{a * common // b}/{common} + {c * common // d}/{common}',
                      'explanation': f'Rewrite both with the common denominator {common}.'},
                     {'equation': f'{a * common // b + c * common // d}/{common} = {total}',
                      'explanation': 'Add the tops; simplify the total.'}]
            return {'text': f"The verified answer is {drill['answer']}.", 'steps': steps, 'answer': drill['answer']}
        if '/' in drill.get('equation', '') and '=' not in drill.get('equation', ''):
            value = expression(drill['equation'])
            g = math.gcd(int(value.p), int(value.q))
            steps = [{'equation': str(value),
                      'explanation': f'Divide top and bottom by {g}.' if g > 1 else 'Already in simplest form.'}]
            return {'text': f"The verified answer is {drill['answer']}.", 'steps': steps, 'answer': drill['answer']}
        result = solve(drill['equation'])
        steps = [{'equation': s.get('equation', ''), 'explanation': s.get('explanation', '')} for s in result.get('steps', [])[:8]]
        return {'text': f"The verified answer is {drill['answer']}.", 'steps': steps, 'answer': drill['answer']}
    except MathError:
        return {'text': f"The verified answer is {drill.get('answer', '')}.", 'steps': [], 'answer': drill.get('answer', '')}


def prompt_for(drill, island):
    if drill.get('kind') == 'spot_mistake':
        return "Mia shows her working with one slip — enter the wrong line number."
    if drill.get('kind') == 'comparison':
        return 'Compare the two fractions — enter <, = or >.'
    if island.get('topic') == 'graphs' or island.get('kind') == 'graph':
        return 'Find the x-intercept (where y = 0).'
    if island.get('topic') == 'fractions' and 'Compare' in drill.get('equation', ''):
        return 'Compare the two fractions — enter <, = or >.'
    if '+' in drill.get('equation', '') or '/' in drill.get('equation', ''):
        return 'Find the value. Enter a fraction like 3/2 if you need to.'
    return 'Find x. Enter an integer, decimal, or fraction.'


def public_drill(drill, number, island):
    if not drill:
        return None
    out = {'number': drill.get('number') or number, 'equation': drill['equation'], 'hint': drill.get('hint', ''),
           'difficulty': drill.get('difficulty', 1), 'kind': drill.get('kind', 'value'),
           'prompt': prompt_for(drill, island), 'lifelines': list(drill.get('lifelines') or [])}
    if drill.get('kind') == 'spot_mistake':
        out['steps'] = list(drill.get('steps') or [])
    return out


def public_journey(journey: Journey):
    islands = journey.islands or []
    island = islands[journey.island_index] if journey.island_index < len(islands) else {}
    return {'id': journey.id, 'state': journey.state, 'island_index': journey.island_index,
            'islands': [{'key': i.get('key'), 'title': i.get('title'), 'subtitle': i.get('subtitle'),
                         'topic': i.get('topic'), 'state': i.get('state'), 'gems': i.get('gems', 0),
                         'asked': i.get('asked', 0)} for i in islands],
            'gems_needed': journey.gems_needed, 'questions_done': journey.questions_done,
            'correct_count': journey.correct_count, 'assists': journey.assists,
            'current': public_drill(journey.current, journey.questions_done + 1, island),
            'trace': journey.trace or [], 'verdict': journey.verdict}


def _seen_equations(db: Session, journey: Journey):
    seen = {entry['equation'] for entry in (journey.log or []) if entry.get('equation')}
    if journey.current and journey.current.get('equation'):
        seen.add(journey.current['equation'])
    return seen | recent_drill_equations(db, journey.user_id)


def serve_next(db: Session, journey: Journey):
    """Queue the next continuous question for the current island."""
    # Deep copy: a shallow list shares the nested island dicts with the ORM
    # snapshot, so in-place gem updates would never reach the UPDATE.
    islands = copy.deepcopy(journey.islands or [])
    island = islands[journey.island_index]
    history = tuple({'correct': e['correct'], 'kind': e.get('kind')} for e in (journey.log or []) if e.get('island') == island['key'])
    seen = _seen_equations(db, journey)
    base = 2 if island['kind'] == 'boss' else 1
    difficulty = min(3, base + island.get('gems', 0))
    island['difficulty'] = difficulty
    spot = guardian_spot(island, seen, history)
    if spot is not None:
        spot['lifelines'] = []
        spot['number'] = journey.questions_done + 1
        journey.current = spot
        journey.islands = islands
        return spot
    drill = generate_island_drill(island, difficulty, seen, history)
    drill['lifelines'] = []
    drill['number'] = journey.questions_done + 1
    journey.current = drill
    journey.islands = islands
    return drill


def start_journey(db: Session, user: User):
    existing = db.scalar(select(Journey).where(Journey.user_id == user.id, Journey.state == 'active'))
    if existing:
        return public_journey(existing)
    plan = diagnose(db, user.id)
    boss_fractions = plan['topic'] == 'fractions'
    islands = []
    for position, definition in enumerate(ISLAND_DEFS):
        islands.append({**definition, 'state': 'current' if position == 0 else 'locked',
                        'gems': 0, 'asked': 0, 'boss_fractions': bool(boss_fractions and definition['kind'] == 'boss')})
    journey = Journey(user_id=user.id, islands=islands, gems_needed=GEMS_NEEDED,
                      max_per_island=MAX_PER_ISLAND, accuracy_before=plan['accuracy_before'])
    journey.trace = [f"Plan: {len(islands)} stages from easy to advanced. {GEMS_NEEDED} correct answers complete each stage.",
                     f"Memory: weakest area is {plan['topic']} ({plan['goal']}) — the final stage focuses on it."]
    journey.log = []
    db.add(journey)
    db.flush()
    serve_next(db, journey)
    journey.trace = list(journey.trace) + [f"Started stage 1: {islands[0]['title']}."]
    db.commit()
    return public_journey(journey)


def abandon_journey(db: Session, user: User):
    row = db.scalar(select(Journey).where(Journey.user_id == user.id, Journey.state == 'active'))
    if row:
        row.state, row.current = 'cancelled', None
        row.updated = int(time.time())
        db.commit()


def finish(journey: Journey):
    accuracy_after = round(journey.correct_count / journey.questions_done, 2) if journey.questions_done else 0.0
    journey.state, journey.current = 'complete', None
    conquered = [i['title'] for i in (journey.islands or []) if i.get('state') == 'conquered']
    cursed = [i['title'] for i in (journey.islands or []) if i.get('state') == 'cursed']
    gems = sum(i.get('gems', 0) for i in (journey.islands or []))
    if not cursed:
        message = f'Journey complete! All {len(conquered)} stages finished with {gems} correct answers. Accuracy {int(journey.accuracy_before * 100)}% → {int(accuracy_after * 100)}%.'
    else:
        message = (f"Journey complete with {gems} correct answers, but {', '.join(cursed)} still needs practice. "
                   f'Accuracy {int(journey.accuracy_before * 100)}% → {int(accuracy_after * 100)}%. Try the journey again to complete them.')
    journey.verdict = {'treasure': not cursed, 'gems': gems, 'accuracy_before': journey.accuracy_before,
                       'accuracy_after': accuracy_after, 'questions': journey.questions_done,
                       'assists': journey.assists, 'message': message,
                       'islands': [{'title': i.get('title'), 'state': i.get('state'), 'gems': i.get('gems', 0)} for i in (journey.islands or [])]}
    journey.trace = list(journey.trace or []) + ['Result: ' + message]


def turn_out(journey: Journey, correct: bool, message: str, event=None, advanced=True):
    body = public_journey(journey)
    return {'correct': correct, 'message': message, 'event': event, 'advanced': advanced,
            **{k: v for k, v in body.items() if k != 'id'}}


def answer_journey(db: Session, user: User, journey_id: str, answer: str):
    journey = db.scalar(select(Journey).where(Journey.id == journey_id).with_for_update())
    if not journey or journey.user_id != user.id:
        raise HTTPException(404, 'Journey not found.')
    if journey.state != 'active' or not journey.current:
        raise HTTPException(409, 'This voyage is already complete.')
    current = journey.current
    islands = copy.deepcopy(journey.islands or [])
    island = islands[journey.island_index]
    is_spot = current.get('kind') == 'spot_mistake'
    if is_spot:
        correct, feedback = grade_spot(current, answer)
    elif current.get('kind') == 'comparison':
        correct = answer.strip() == current['answer']
        feedback = ''
    else:
        value = answer_value(answer)
        if value.free_symbols:
            raise MathError('Enter a number or fraction, such as 4 or 3/2.')
        correct = value == expression(current['answer'])
        feedback = ''
    journey.questions_done += 1
    island['asked'] = island.get('asked', 0) + 1
    log = list(journey.log or [])
    log.append({'island': island['key'], 'equation': current['equation'], 'correct': bool(correct),
                'kind': current.get('kind', 'value'), 'assisted': bool(current.get('revealed'))})
    journey.log = log
    trace = list(journey.trace or [])
    event = None
    if correct:
        journey.correct_count += 1
        if current.get('revealed'):
            message = f'Correct — but the shown solution solved this one, so it does not count. ({current["equation"]} = {current["answer"]}).'
            trace.append(f"{island['title']} Q{island['asked']}: correct with solution shown — does not count.")
        else:
            island['gems'] = island.get('gems', 0) + 1
            gems = island['gems']
            message = feedback if is_spot else f'Correct! {gems} of {journey.gems_needed} on {island["title"]}.'
            if is_spot:
                message = f'{feedback} {gems} of {journey.gems_needed} on {island["title"]}.'
            trace.append(f"{island['title']} Q{island['asked']}: correct ({current['equation']}). Progress: {gems}/{journey.gems_needed}.")
            if gems >= journey.gems_needed:
                island['state'] = 'conquered'
                event = f"conquered:{island['title']}"
                trace.append(f"{island['title']} complete! Moving on.")
    else:
        misses = int(current.get('misses') or 0) + 1
        current = dict(current)
        current['misses'] = misses
        journey.current = current
        if island['asked'] >= journey.max_per_island and island.get('state') != 'conquered':
            island['state'] = 'cursed'
            event = f"passage:{island['title']}"
            trace.append(f"{island['title']} still needs practice after {journey.max_per_island} tries — moving on.")
            taught = True
        else:
            taught = misses >= MAX_MISSES
        if taught:
            if is_spot:
                message = feedback + ' Study the slip and try the next question.'
            else:
                message = f"Not quite — the verified answer is {current['answer']}. Study it and try the next question."
            trace.append(f"{island['title']} Q{island['asked']}: incorrect ({current['equation']}). Verified answer was {current['answer']}.")
        else:
            message = f'Not quite — try again. (Attempt {misses} of {MAX_MISSES}.)'
            trace.append(f"{island['title']} Q{island['asked']}: incorrect, attempt {misses} of {MAX_MISSES} — same question again.")
            journey.islands = islands
            journey.trace = trace
            journey.updated = int(time.time())
            db.commit()
            return turn_out(journey, False, message, event, advanced=False)
    journey.islands = islands
    journey.trace = trace
    if event is not None:
        journey.island_index += 1
        if journey.island_index >= len(islands):
            finish(journey)
            journey.updated = int(time.time())
            db.commit()
            return turn_out(journey, bool(correct), message, event)
        islands = copy.deepcopy(journey.islands or [])
        nxt = islands[journey.island_index]
        nxt['state'] = 'current'
        journey.islands = islands
        journey.trace = list(journey.trace) + [f"Started stage {journey.island_index + 1}: {nxt['title']}."]
    serve_next(db, journey)
    journey.updated = int(time.time())
    db.commit()
    return turn_out(journey, bool(correct), message, event)


def use_lifeline(db: Session, user: User, journey_id: str, kind: str):
    if kind not in ('hint', 'nudge', 'reveal'):
        raise HTTPException(422, 'Unknown lifeline. Choose hint, nudge, or reveal.')
    journey = db.scalar(select(Journey).where(Journey.id == journey_id).with_for_update())
    if not journey or journey.user_id != user.id:
        raise HTTPException(404, 'Journey not found.')
    if journey.state != 'active' or not journey.current:
        raise HTTPException(409, 'This voyage is already complete.')
    current = dict(journey.current)
    used = list(current.get('lifelines') or [])
    if kind == 'hint':
        if 'hint' not in used:
            used.append('hint')
        current['lifelines'] = used
        journey.current = current
        db.commit()
        return {'kind': 'hint', 'text': current.get('hint', ''), 'step': None, 'steps': [],
                'answer': None, 'revealed': False}
    if kind == 'nudge':
        nudge = guiding_nudge(current)
        if 'nudge' not in used:
            used.append('nudge')
        current['lifelines'] = used
        journey.current = current
        db.commit()
        return {'kind': 'nudge', 'text': nudge['text'], 'step': nudge['step'], 'steps': [],
                'answer': None, 'revealed': False}
    solution = reveal_solution(current)
    current['revealed'] = True
    if 'reveal' not in used:
        used.append('reveal')
        journey.assists += 1
    current['lifelines'] = used
    journey.current = current
    db.commit()
    return {'kind': 'reveal', 'text': solution['text'], 'step': None, 'steps': solution['steps'],
            'answer': solution['answer'], 'revealed': True}
