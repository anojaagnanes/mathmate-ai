"""Autonomous Mistake-to-Mastery missions (Mia Autopilot).

One entry point, one bounded loop: perceive the student's persisted
history, diagnose a single weakness, plan drills with an exit test, adapt
difficulty from live answers, then declare a verdict with before/after
proof. Every drill answer is graded by the deterministic solver; the
agent never grades by prose and never invents a result.
"""
import re
import secrets
import sympy as sp
import time
from collections import Counter
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from .math_parser import MathError
from .math_runtime import solve, expression, answer_value
from .models import Mission, QuizAttempt, QuizQuestion, SolutionFeedback, TopicMastery, User
from .work_review import review_work
from .agents.practice import PracticeAgent

EXIT_WINS = 3
MAX_DRILLS = 10
MAX_REPLANS = 2
MAX_WRONG = 3

# Stored error code -> (topic, drill category, student-facing label).
ERROR_TARGETS = {
    'fraction_addition': ('fractions', 'addition', 'adding fractions with different denominators'),
    'fraction_equivalence': ('fractions', 'equivalence', 'simplifying to equivalent fractions'),
    'fraction_comparison': ('fractions', 'comparison', 'comparing fraction sizes'),
    'inverse_operation': ('equations', 'linear', 'moving terms with the opposite operation'),
    'changed_solution': ('equations', 'linear', 'keeping both sides balanced'),
    'one_side_changed': ('equations', 'linear', 'changing only one side of the equation'),
    'division_by_zero': ('equations', 'linear', 'avoiding division by zero'),
    'unsupported_input': ('equations', 'linear', 'writing one clear equality per line'),
}


def diagnose(db: Session, user_id: str):
    """Read-only perception over persisted reviews and quiz attempts."""
    feedback = list(db.scalars(select(SolutionFeedback).where(SolutionFeedback.user_id == user_id)))
    counts: Counter = Counter()
    for row in feedback:
        result = row.result or {}
        if result.get('valid') is False or result.get('status') == 'incorrect_step_detected':
            nested = result.get('work_review') or {}
            counts[result.get('error_code') or result.get('error_category') or nested.get('error_category') or 'changed_solution'] += 1
    pairs = list(db.execute(select(QuizAttempt, QuizQuestion).join(QuizQuestion, QuizAttempt.question_id == QuizQuestion.id).where(QuizAttempt.user_id == user_id).order_by(QuizAttempt.submitted_at, QuizAttempt.id)))
    by_topic: dict[str, list] = {}
    for attempt, question in pairs:
        by_topic.setdefault(question.topic_id, []).append(attempt)
    candidates: dict[str, float] = {}
    for topic, attempts in by_topic.items():
        if len(attempts) >= 3:
            recent = attempts[-5:]
            candidates[topic] = sum(a.correct for a in recent) / len(recent)
    recent_all = [a for a, _ in pairs[-10:]]
    accuracy_before = round(sum(a.correct for a in recent_all) / len(recent_all), 2) if recent_all else 0.0
    last_done = db.scalar(select(Mission).where(Mission.user_id == user_id, Mission.state == 'complete').order_by(Mission.updated.desc()))
    just_mastered = last_done.error_code if last_done and (last_done.verdict or {}).get('mastered') and last_done.error_code else None
    for code, _ in counts.most_common():
        if code == just_mastered:
            continue
        if code in ERROR_TARGETS:
            topic, category, label = ERROR_TARGETS[code]
            return {'error_code': code, 'topic': topic, 'category': category,
                    'goal': f'Fix {label}: {counts[code]} recent mistake{"s" if counts[code] != 1 else ""} found.',
                    'errors_found': dict(counts), 'accuracy_before': accuracy_before,
                    'skipped_mastered': just_mastered}
    if candidates:
        weak_topic = min(candidates, key=candidates.get)
        return {'error_code': None, 'topic': weak_topic, 'category': 'linear',
                'goal': f'Build consistency in {weak_topic}: recent accuracy {int(candidates[weak_topic] * 100)}%.',
                'errors_found': dict(counts), 'accuracy_before': accuracy_before,
                'skipped_mastered': just_mastered}
    return {'error_code': None, 'topic': 'equations', 'category': 'linear',
            'goal': 'Build consistency in equations with a short adaptive set.',
            'errors_found': dict(counts), 'accuracy_before': accuracy_before,
            'skipped_mastered': just_mastered}


def generate_linear_drill(difficulty, seen):
    for _ in range(50):
        level = min(3, max(1, difficulty))
        answer = secrets.randbelow(13) - 6
        a, b = secrets.randbelow(3 * level) + 1, secrets.randbelow(10 * level) - 5
        equation = f'{a}x + ({b}) = {a * answer + b}'
        if level == 3:
            equation = f'{a+2}x + ({b}) = 2x + ({a * answer + b})'
        if equation in seen:
            continue
        try:
            result = solve(equation)
        except MathError:
            continue
        if result.get('verified') and result.get('kind') == 'unique':
            steps = result.get('steps', [])
            return {'equation': equation, 'answer': result['solution'], 'kind': 'value',
                    'difficulty': level, 'hint': steps[1]['explanation'] if len(steps) > 1 else 'Isolate x by reversing each operation.'}
    raise MathError('Could not generate a verified drill. Please try again.')


def generate_drill(topic, category, difficulty, seen, history=()):
    if topic == 'fractions':
        question = PracticeAgent().generate(category, history, seen)
        if not question:
            raise MathError('The verified practice pool is exhausted for this mission.')
        return {'equation': question['equation'], 'answer': question['answer'], 'kind': question['kind'],
                'difficulty': difficulty, 'hint': question['hint']}
    return generate_linear_drill(difficulty, seen)


def _linear_spot_drill(difficulty, seen):
    """Role reversal: Mia shows linear working with exactly one planted slip.

    The first lines are taken from the verified solver; the final shown line
    claims a value one away from the verified solution. The slip position
    alternates so the answer is not a constant. Returns None unless the
    production reviewer flags exactly the planted line.
    """
    base = generate_linear_drill(difficulty, seen)
    result = solve(base['equation'])
    steps = result.get('steps', [])
    if result.get('kind') != 'unique' or len(steps) < 2:
        return None
    solution = expression(result['solution'])
    if solution.free_symbols:
        return None
    wrong_value = solution + 1
    if len(seen) % 2 == 0:
        shown = [steps[0]['equation'], steps[1]['equation'], f'x = {wrong_value}']
        wrong_line = 3
    else:
        shown = [steps[0]['equation'], f'x = {wrong_value}']
        wrong_line = 2
    review = review_work(shown)
    if review.get('status') != 'incorrect_step_detected' or review.get('first_incorrect_step') != wrong_line:
        return None
    return {'equation': shown[0], 'answer': str(wrong_line), 'kind': 'spot_mistake',
            'difficulty': difficulty,
            'hint': 'Mia worked this out but slipped on exactly one line. Enter the wrong line number.',
            'steps': shown, 'wrong_line': wrong_line,
            'explanation': f'Line {wrong_line} claims x = {wrong_value}, but the verified solution is x = {result["solution"]}. The earlier lines keep the same solution; this line loses it.'}


def _fraction_spot_drill(seen, history):
    """Role reversal for fraction addition: Mia adds correctly, then restates
    the total with a different value on line 2. Returns None unless the
    production reviewer flags exactly line 2."""
    question = PracticeAgent().generate('addition', history, seen)
    if not question:
        return None
    parts = question['equation'].split('+')
    if len(parts) != 2:
        return None
    try:
        target = expression(parts[0].strip()) + expression(parts[1].strip())
    except MathError:
        return None
    if not getattr(target, 'is_Rational', False):
        return None
    wrong = sp.Rational(target.p + 1, target.q)
    shown = [f"{question['equation']} = {target}", f'{target} = {wrong}']
    review = review_work(shown)
    if review.get('status') != 'incorrect_step_detected' or review.get('first_incorrect_step') != 2:
        return None
    return {'equation': question['equation'], 'answer': '2', 'kind': 'spot_mistake',
            'difficulty': question.get('difficulty', 1),
            'hint': 'Mia worked this out but slipped on exactly one line. Enter the wrong line number.',
            'steps': shown, 'wrong_line': 2,
            'explanation': f'Line 1 correctly totals {target}, but line 2 restates it as {wrong}, which has a different exact value.'}


def generate_spot_drill(topic, category, difficulty, seen, history=()):
    """One role-reversal round per mission, or None when the topic has no
    supported shape. Comparison and equivalence drills are out of scope and
    fall back to normal drills. Never raises: unverifiable content must not
    break the mission loop."""
    try:
        if topic == 'fractions':
            if category == 'addition':
                return _fraction_spot_drill(seen, history)
            return None
        return _linear_spot_drill(difficulty, seen)
    except MathError:
        return None


def grade_spot(drill, answer):
    """Grade a role-reversal round: the answer is the wrong line number.

    A numeric guess that misses is simply wrong, matching the other drill
    kinds; only input with no line number at all is rejected as malformed.
    """
    steps = drill.get('steps') or []
    match = re.search(r'\d+', (answer or '').strip())
    if not match:
        raise MathError('Enter the wrong line number, such as 2.')
    wrong = int(drill.get('wrong_line') or 0)
    explanation = drill.get('explanation') or ''
    if int(match.group()) == wrong:
        return True, f"Correct — line {wrong} is where Mia slipped. {explanation}"
    return False, f"Not quite — Mia slipped on line {wrong}. {explanation}"


def worked_example(topic, category):
    drill = generate_drill(topic, category, 1, set())
    try:
        result = solve(drill['equation'])
        steps = [{'equation': s.get('equation', ''), 'explanation': s.get('explanation', '')} for s in result.get('steps', [])[:8]]
        verified = bool(result.get('verified'))
    except MathError:
        steps, verified = [{'equation': drill['equation'], 'explanation': drill['hint']}], False
    return {'equation': drill['equation'], 'answer': drill['answer'], 'steps': steps, 'verified': verified}


def public_drill(drill, number):
    if not drill:
        return None
    out = {'number': number, 'equation': drill['equation'], 'hint': drill.get('hint', ''),
           'difficulty': drill.get('difficulty', 1), 'kind': drill.get('kind', 'value')}
    if drill.get('kind') == 'spot_mistake':
        # Mia's working is shown; the wrong line number stays server-side.
        out['steps'] = list(drill.get('steps') or [])
    return out


def public_mission(mission: Mission):
    return {'id': mission.id, 'goal': mission.goal, 'topic': mission.topic, 'error': mission.error_code,
            'state': mission.state, 'difficulty': mission.difficulty, 'drills_done': mission.drills_done,
            'consecutive': mission.consecutive, 'exit_wins': mission.exit_wins, 'max_drills': mission.max_drills,
            'example': mission.example, 'current': public_drill(mission.current, mission.drills_done + 1),
            'trace': mission.trace or [], 'verdict': mission.verdict}


def recent_drill_equations(db: Session, user_id: str, exclude_id: str | None = None, limit: int = 5):
    """Equations asked in recent missions, so a restart feels fresh instead of repeated."""
    query = select(Mission).where(Mission.user_id == user_id)
    if exclude_id:
        query = query.where(Mission.id != exclude_id)
    seen = set()
    for row in db.scalars(query.order_by(Mission.updated.desc()).limit(limit)):
        for d in (row.drills or [])[-MAX_DRILLS:]:
            if d.get('equation'):
                seen.add(d['equation'])
        if row.example and row.example.get('equation'):
            seen.add(row.example['equation'])
    return seen


def fresh_drill(topic, category, difficulty, seen_extended, seen_minimal, history=()):
    """Prefer an unseen drill, but repeat rather than break the mission loop."""
    try:
        return generate_drill(topic, category, difficulty, seen_extended, history)
    except MathError:
        return generate_drill(topic, category, difficulty, seen_minimal, history)


def start_mission(db: Session, user: User):
    existing = db.scalar(select(Mission).where(Mission.user_id == user.id, Mission.state == 'active'))
    if existing:
        return public_mission(existing)
    plan = diagnose(db, user.id)
    difficulty = 1
    if plan['topic'] in ('equations', 'graphs'):
        row = db.scalar(select(TopicMastery).where(TopicMastery.user_id == user.id, TopicMastery.topic_id == plan['topic']))
        if row:
            difficulty = min(3, max(1, row.difficulty))
    mission = Mission(user_id=user.id, goal=plan['goal'], topic=plan['topic'], error_code=plan['error_code'],
                      difficulty=difficulty, exit_wins=EXIT_WINS, max_drills=MAX_DRILLS, max_replans=MAX_REPLANS,
                      accuracy_before=plan['accuracy_before'])
    mission.example = worked_example(plan['topic'], plan['category'])
    minimal = {mission.example['equation']}
    mission.current = fresh_drill(plan['topic'], plan['category'], difficulty,
                                  minimal | recent_drill_equations(db, user.id), minimal)
    mission.trace = [f"Diagnosis: {plan['goal']} (history accuracy {int(plan['accuracy_before'] * 100)}%).",
                     f"Plan: worked example, then up to {MAX_DRILLS} adaptive drills. Exit test: {EXIT_WINS} correct in a row, no hints."]
    if plan.get('skipped_mastered'):
        mission.trace.append(f"Memory: '{plan['skipped_mastered']}' was already mastered — targeting the next weakness instead.")
    mission.drills, mission.verdict = [], None
    db.add(mission)
    db.commit()
    return public_mission(mission)


def finish(mission: Mission, mastered: bool, teaching: bool = False):
    accuracy_after = round(mission.correct_count / mission.drills_done, 2) if mission.drills_done else 0.0
    mission.state, mission.current = 'complete', None
    missed = []
    for d in (mission.drills or []):
        if d.get('correct'):
            continue
        if d.get('kind') == 'spot_mistake':
            missed.append({'equation': d['equation'], 'answer': f"line {d.get('answer', '')}", 'hint': d.get('hint', '')})
        else:
            missed.append({'equation': d['equation'], 'answer': d.get('answer', ''), 'hint': d.get('hint', '')})
    if mastered:
        message = f'Mastery achieved: {mission.exit_wins} correct in a row. Accuracy {int(mission.accuracy_before * 100)}% → {int(accuracy_after * 100)}%.'
    elif teaching:
        message = f'Stopped after {MAX_WRONG} wrong answers. Study the {len(missed)} verified answers below, then start a gentler mission.'
    else:
        message = f'Not yet mastered after {mission.drills_done} drills. Accuracy {int(mission.accuracy_before * 100)}% → {int(accuracy_after * 100)}%. Try a gentler mission next.'
    mission.verdict = {'mastered': mastered, 'accuracy_before': mission.accuracy_before,
                       'accuracy_after': accuracy_after, 'drills': mission.drills_done, 'replans': mission.replans,
                       'message': message, 'teaching': missed if teaching else []}
    trace = list(mission.trace or [])
    trace.append('Verdict: ' + mission.verdict['message'])
    mission.trace = trace


def answer_mission(db: Session, user: User, mission_id: str, answer: str):
    mission = db.scalar(select(Mission).where(Mission.id == mission_id).with_for_update())
    if not mission or mission.user_id != user.id:
        raise HTTPException(404, 'Mission not found.')
    if mission.state != 'active' or not mission.current:
        raise HTTPException(409, 'This mission is already complete.')
    current = mission.current
    is_spot = current.get('kind') == 'spot_mistake'
    spot_feedback = None
    if is_spot:
        correct, spot_feedback = grade_spot(current, answer)
    elif current.get('kind') == 'comparison':
        correct = answer.strip() == current['answer']
    else:
        value = answer_value(answer)
        if value.free_symbols:
            raise MathError('Enter a number or fraction, such as 4 or 3/2.')
        correct = value == expression(current['answer'])
    mission.drills_done += 1
    log = list(mission.drills or [])
    log.append({'number': mission.drills_done, 'equation': current['equation'], 'correct': bool(correct),
                'answer': current.get('answer', ''), 'hint': current.get('explanation') or current.get('hint', ''),
                'kind': current.get('kind', 'value')})
    mission.drills = log
    trace = list(mission.trace or [])
    if correct:
        mission.correct_count += 1
        mission.consecutive += 1
        if is_spot:
            trace.append(f"Turn {mission.drills_done}: spot-the-mistake correct — found Mia's slip on line {current['answer']}. Streak: {mission.consecutive}.")
        else:
            trace.append(f"Turn {mission.drills_done}: correct ({current['equation']}). Streak: {mission.consecutive}.")
        if mission.consecutive >= mission.exit_wins:
            mission.trace = trace
            finish(mission, True)
            mission.updated = int(time.time())
            db.commit()
            return turn_out(mission, True, 'Exit test passed.' + (f' {spot_feedback}' if is_spot else ''))
        if mission.consecutive >= 2 and mission.difficulty < 3:
            mission.difficulty += 1
            trace.append(f"Two in a row — raising difficulty to {mission.difficulty}.")
        message = spot_feedback if is_spot else 'Correct. The streak continues.'
    else:
        mission.consecutive = 0
        if is_spot:
            trace.append(f"Turn {mission.drills_done}: spot-the-mistake missed — Mia's slip was line {current['answer']}; streak reset.")
        else:
            trace.append(f"Turn {mission.drills_done}: incorrect ({current['equation']}). Verified answer was {current['answer']}; streak reset.")
        if mission.drills_done - mission.correct_count >= MAX_WRONG:
            trace.append(f"{MAX_WRONG} wrong answers reached — stopping drills and revealing the verified answers with explanations.")
            mission.trace = trace
            finish(mission, False, teaching=True)
            mission.updated = int(time.time())
            db.commit()
            return turn_out(mission, False, 'Three wrong answers — mission stopped. Study the verified answers below.')
        if mission.drills_done >= 4 and mission.replans < mission.max_replans and mission.difficulty > 1:
            old = mission.difficulty
            mission.difficulty, mission.replans = old - 1, mission.replans + 1
            trace.append(f"Re-plan {mission.replans}: accuracy low — difficulty {old} → {mission.difficulty}, gentler drills queued.")
        if is_spot:
            message = spot_feedback + ' The streak resets; study the example step and try the next drill.'
        else:
            message = f"Not quite — the verified answer is {current['answer']}. Study the example step and try the next drill."
    if mission.drills_done >= mission.max_drills:
        mission.trace = trace
        finish(mission, False)
        mission.updated = int(time.time())
        db.commit()
        return turn_out(mission, False, 'Mission drills exhausted.')
    seen = {d['equation'] for d in log} | ({mission.example['equation']} if mission.example else set())
    fresh_seen = seen | recent_drill_equations(db, mission.user_id, exclude_id=mission.id)
    history = tuple({'correct': d['correct']} for d in log[-3:])
    category = dict(fractions='addition').get(mission.topic, 'linear')
    if mission.topic == 'fractions' and (mission.error_code or '').startswith('fraction_'):
        category = mission.error_code.split('_', 1)[1]
    spot = None
    if mission.consecutive >= 2 and not any(d.get('kind') == 'spot_mistake' for d in log):
        # Role reversal, once per mission: Mia shows her working with one slip.
        spot = generate_spot_drill(mission.topic, category, mission.difficulty, fresh_seen, history)
    if spot is not None:
        trace.append("Role reversal: Mia shows her working with exactly one slip. Enter the wrong line number.")
        mission.current = spot
    else:
        mission.current = fresh_drill(mission.topic, category, mission.difficulty, fresh_seen, seen, history)
    mission.trace, mission.updated = trace, int(time.time())
    db.commit()
    return turn_out(mission, bool(correct), message)


def turn_out(mission: Mission, correct: bool, message: str):
    return {'correct': correct, 'message': message, 'consecutive': mission.consecutive,
            'drills_done': mission.drills_done, 'difficulty': mission.difficulty, 'state': mission.state,
            'current': public_drill(mission.current, mission.drills_done + 1),
            'trace': mission.trace or [], 'verdict': mission.verdict}
