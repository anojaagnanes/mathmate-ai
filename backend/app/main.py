import io
import secrets
import time
from typing import Annotated
from PIL import Image, UnidentifiedImageError
from fastapi import FastAPI, Depends, HTTPException, Request, Response, UploadFile
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from .config import settings
from .db import get_db
from .models import *
from .schemas import Register, Login, Equation, Steps, Answer, Chat, Preferences, Graph
from .security import current_user, csrf, rate_limit, passwords, issue, digest, revoke_family
from .math_parser import MathError
from .math_runtime import solve, analyze, expression
from .adaptive import recommend
from .providers import get_provider
from . import schemas as dto
from collections import Counter

app = FastAPI(title='MathMate AI', version='0.1.0')
app.add_middleware(CORSMiddleware, allow_origins=[settings.frontend_origin], allow_credentials=True, allow_methods=['GET', 'POST', 'PUT'], allow_headers=['Authorization', 'Content-Type', 'X-MathMate-Client'])
DB = Annotated[Session, Depends(get_db)]
Student = Annotated[User, Depends(current_user)]
prefix = '/api/v1'


@app.exception_handler(MathError)
async def math_error(request, exc):
    return JSONResponse(status_code=422, content={'detail': str(exc)})


@app.middleware('http')
async def headers(request, call_next):
    response = await call_next(request)
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Cache-Control'] = 'no-store'
    return response


@app.get(prefix + '/health')
def health():
    return {'status': 'ok', 'ai_provider': settings.ai_provider}


@app.post(prefix + '/auth/register', dependencies=[Depends(csrf), Depends(rate_limit)], status_code=201, response_model=dto.AuthOut)
def register(data: Register, response: Response, db: DB):
    user = User(email=str(data.email).lower(), name=data.name.strip() or 'Learner', password_hash=passwords.hash(data.password))
    db.add(user)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, 'Unable to register with this email. Try signing in.')
    db.add(UserSettings(user_id=user.id))
    return issue(db, user, response)


@app.post(prefix + '/auth/login', dependencies=[Depends(csrf), Depends(rate_limit)], response_model=dto.AuthOut)
def login(data: Login, response: Response, db: DB):
    user = db.scalar(select(User).where(User.email == str(data.email).lower()))
    # Always perform a password hash check to reduce account enumeration by timing.
    hashed = user.password_hash if user else DUMMY_HASH
    valid = passwords.verify(data.password, hashed)
    if not user or not valid:
        raise HTTPException(401, 'Email or password is incorrect.')
    return issue(db, user, response)


DUMMY_HASH = passwords.hash(secrets.token_urlsafe(32))


@app.post(prefix + '/auth/refresh', dependencies=[Depends(csrf)], response_model=dto.AuthOut)
def refresh(request: Request, response: Response, db: DB):
    row = db.get(RefreshToken, digest(request.cookies.get('mathmate_refresh', '')))
    if not row or row.expires < time.time():
        raise HTTPException(401, 'Session expired.')
    # Serialize family mutations on PostgreSQL so logout cannot race a rotation.
    db.scalar(select(User).where(User.id == row.user_id).with_for_update())
    consumed = db.execute(update(RefreshToken).where(RefreshToken.digest == row.digest, RefreshToken.revoked.is_(False)).values(revoked=True)).rowcount
    if consumed != 1:
        revoke_family(db, row.family)
        raise HTTPException(401, 'Refresh token reuse detected. Sign in again.')
    return issue(db, db.get(User, row.user_id), response, row.family)


@app.post(prefix + '/auth/logout', dependencies=[Depends(csrf)])
def logout(request: Request, response: Response, db: DB):
    row = db.get(RefreshToken, digest(request.cookies.get('mathmate_refresh', '')))
    if row:
        db.scalar(select(User).where(User.id == row.user_id).with_for_update())
        revoke_family(db, row.family)
    response.delete_cookie('mathmate_refresh', path='/api/v1/auth', secure=settings.secure_cookies, httponly=True, samesite='strict')
    return {'ok': True}


@app.get(prefix + '/me', response_model=dto.UserOut)
def me(user: Student):
    return {'id': user.id, 'name': user.name, 'email': user.email}


@app.get(prefix + '/topics', response_model=list[dto.TopicOut])
def topics(user: Student, db: DB):
    return [{'id': t.id, 'title': t.title, 'description': t.description, 'lessons': [{'id': l.id, 'title': l.title, 'equation': l.equation} for l in db.scalars(select(Lesson).where(Lesson.topic_id == t.id))]} for t in db.scalars(select(Topic))]


@app.get(prefix + '/lessons/{lesson_id}', response_model=dto.LessonOut)
def lesson(lesson_id: str, user: Student, db: DB):
    row = db.get(Lesson, lesson_id)
    if not row:
        raise HTTPException(404, 'Lesson not found.')
    return {'id': row.id, 'title': row.title, 'equation': row.equation, 'solution': solve(row.equation)}


@app.post(prefix + '/lessons/{lesson_id}/complete')
def complete(lesson_id: str, user: Student, db: DB):
    if not db.get(Lesson, lesson_id):
        raise HTTPException(404, 'Lesson not found.')
    row = db.scalar(select(LearningSession).where(LearningSession.user_id == user.id, LearningSession.lesson_id == lesson_id))
    if not row:
        row = LearningSession(user_id=user.id, lesson_id=lesson_id)
        db.add(row)
    row.completed = True
    db.commit()
    return {'completed': True}


@app.post(prefix + '/math/solve', response_model=dto.SolutionOut)
def math_solve(data: Equation, user: Student):
    return solve(data.equation, data.variable)


@app.post(prefix + '/math/validate', response_model=dto.FeedbackOut)
def validate(data: Steps, user: Student, db: DB):
    result = analyze(data.steps)
    db.add(SolutionFeedback(user_id=user.id, result=result))
    db.commit()
    return result


@app.post(prefix + '/math/graph', response_model=dto.GraphOut)
def graph(data: Graph, user: Student):
    return {'points': [{'x': n, 'y': data.slope * n + data.intercept} for n in range(-10, 11)], 'x_intercept': -data.intercept / data.slope if data.slope else None}


def mastery(db, user_id, topic_id):
    row = db.scalar(select(TopicMastery).where(TopicMastery.user_id == user_id, TopicMastery.topic_id == topic_id))
    if not row:
        row = TopicMastery(user_id=user_id, topic_id=topic_id, difficulty=1, accuracy=0)
        db.add(row)
        db.flush()
    return row


@app.post(prefix + '/quizzes', response_model=dto.QuestionOut)
def quiz(user: Student, db: DB, topic_id: str = 'equations'):
    if topic_id not in ('equations', 'graphs'):
        raise HTTPException(422, 'Unknown topic.')
    level = mastery(db, user.id, topic_id).difficulty
    answer = secrets.randbelow(13) - 6
    a, b = secrets.randbelow(3 * level) + 1, secrets.randbelow(10 * level) - 5
    equation = f'{a}x + ({b}) = {a * answer + b}'
    if level == 3:
        equation = f'{a+2}x + ({b}) = 2x + ({a * answer + b})'
    if topic_id == 'graphs':
        equation = f'{a}x + ({-a * answer}) = 0'
    row = QuizQuestion(user_id=user.id, topic_id=topic_id, equation=equation, difficulty=level)
    db.add(row)
    db.commit()
    return {'id': row.id, 'equation': equation, 'difficulty': level, 'prompt': 'Find the x-intercept (where y = 0).' if topic_id == 'graphs' else 'Find x. Enter an integer, decimal, or fraction.'}


def owned_question(db, user, question_id):
    q = db.scalar(select(QuizQuestion).where(QuizQuestion.id == question_id).with_for_update())
    if not q or q.user_id != user.id:
        raise HTTPException(404, 'Question not found.')
    return q


@app.post(prefix + '/quizzes/{question_id}/hint')
def hint(question_id: str, user: Student, db: DB):
    q = owned_question(db, user, question_id)
    if db.scalar(select(QuizAttempt).where(QuizAttempt.question_id == q.id)):
        raise HTTPException(409, 'This question has already been answered.')
    q.hinted = True
    db.commit()
    return {'hint': solve(q.equation)['steps'][1]['explanation']}


@app.post(prefix + '/quizzes/{question_id}/submit', response_model=dto.SubmissionOut)
def submit(question_id: str, data: Answer, user: Student, db: DB):
    q = owned_question(db, user, question_id)
    if db.scalar(select(QuizAttempt).where(QuizAttempt.question_id == q.id)):
        raise HTTPException(409, 'This question has already been answered.')
    result = solve(q.equation)
    value = expression(data.answer)
    if value.free_symbols:
        raise MathError('Enter a number or fraction, such as 4 or 3/2.')
    correct = value == expression(result['solution'])
    attempt = QuizAttempt(user_id=user.id, question_id=q.id, correct=bool(correct), hinted=q.hinted)
    db.add(attempt)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, 'This question has already been answered.')
    db.add(StudentAnswer(attempt_id=attempt.id, answer=data.answer))
    history = list(db.scalars(select(QuizAttempt).join(QuizQuestion).where(QuizAttempt.user_id == user.id, QuizQuestion.topic_id == q.topic_id).order_by(QuizAttempt.submitted_at, QuizAttempt.id)))
    m = mastery(db, user.id, q.topic_id)
    m.difficulty, m.accuracy, reason = recommend(history, m.difficulty)
    rec = db.get(LearningRecommendation, user.id)
    if rec:
        rec.reason = reason
    else:
        db.add(LearningRecommendation(user_id=user.id, reason=reason))
    db.commit()
    return {'correct': bool(correct), 'solution': result, 'recommendation': reason, 'difficulty': m.difficulty}


@app.get(prefix + '/progress', response_model=dto.ProgressOut)
def progress(user: Student, db: DB):
    attempts = list(db.scalars(select(QuizAttempt).where(QuizAttempt.user_id == user.id).order_by(QuizAttempt.submitted_at, QuizAttempt.id)))
    rec = db.get(LearningRecommendation, user.id)
    feedback = list(db.scalars(select(SolutionFeedback).where(SolutionFeedback.user_id == user.id)))
    return {'attempts': len(attempts), 'correct': sum(a.correct for a in attempts), 'hints': sum(a.hinted for a in attempts), 'completed_lessons': list(db.scalars(select(LearningSession.lesson_id).where(LearningSession.user_id == user.id, LearningSession.completed.is_(True)))), 'recommendation': rec.reason if rec else 'Start with The art of balance, then try a short quiz.', 'mastery': [{'topic': m.topic_id, 'accuracy': m.accuracy, 'difficulty': m.difficulty} for m in db.scalars(select(TopicMastery).where(TopicMastery.user_id == user.id))], 'history': [{'number': i + 1, 'correct': int(a.correct), 'hinted': a.hinted} for i, a in enumerate(attempts)], 'reviews': [f.result for f in feedback[-10:]], 'common_errors': sum(not f.result['valid'] for f in feedback), 'error_categories': dict(Counter(f.result.get('error_code') or 'changed_solution' for f in feedback if not f.result['valid']))}


@app.get(prefix + '/settings', response_model=Preferences)
def get_settings(user: Student, db: DB):
    row = db.get(UserSettings, user.id)
    return {'muted': row.muted, 'voice': row.voice}


@app.put(prefix + '/settings', response_model=Preferences)
def save_settings(data: Preferences, user: Student, db: DB):
    row = db.get(UserSettings, user.id)
    row.muted, row.voice = data.muted, data.voice
    db.commit()
    return data


@app.post(prefix + '/tutor/chat', response_model=dto.ChatOut)
async def chat(data: Chat, user: Student, db: DB):
    verified = await run_in_threadpool(solve, data.equation, data.variable)
    provider = get_provider()
    try:
        answer = await provider.explain(data.message, verified)
        mode = provider.name
    except Exception:
        from .providers import MockAIProvider
        answer = await MockAIProvider().explain(data.message, verified)
        mode = 'local fallback — external provider unavailable'
    db.add(TutorMessage(user_id=user.id, question=data.message, answer=answer[:4000]))
    db.commit()
    return {'message': answer, 'mode': mode, 'verified_math': verified}


@app.post(prefix + '/handwriting/upload', response_model=dto.UploadOut)
async def upload(file: UploadFile, user: Student, db: DB):
    raw = await file.read(5 * 1024 * 1024 + 1)
    if len(raw) > 5 * 1024 * 1024:
        raise HTTPException(413, 'Choose an image smaller than 5 MB.')
    if file.content_type not in ('image/jpeg', 'image/png', 'image/webp'):
        raise HTTPException(422, 'Use a PNG, JPEG, or WebP image.')
    try:
        with Image.open(io.BytesIO(raw)) as image:
            if image.format not in ('PNG', 'JPEG', 'WEBP') or max(image.size) > 4096 or min(image.size) < 16:
                raise ValueError()
            width, height = image.size
            expected_mime = {'PNG': 'image/png', 'JPEG': 'image/jpeg', 'WEBP': 'image/webp'}[image.format]
            if file.content_type != expected_mime:
                raise ValueError()
            image.verify()
        # Decode pixels as well as checking headers; truncated files must not reach a provider.
        with Image.open(io.BytesIO(raw)) as image:
            image.load()
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError):
        raise HTTPException(422, 'Invalid image or dimensions outside 16–4096 pixels.')
    row = UploadedSolution(user_id=user.id, filename=(file.filename or 'image')[:255], width=width, height=height)
    db.add(row)
    db.commit()
    provider = get_provider()
    try:
        steps = await provider.transcribe(raw, file.content_type)
    except Exception:
        steps = []
    return {'id': row.id, 'steps': steps, 'mode': 'AI draft — confirm every line' if steps else 'manual', 'message': 'Review every line before confirming.' if steps else 'Automatic transcription is unavailable. Type the original equation and your steps below. The image is not retained.'}


@app.post(prefix + '/handwriting/{upload_id}/confirm', response_model=dto.FeedbackOut)
def confirm(upload_id: str, data: Steps, user: Student, db: DB):
    row = db.scalar(select(UploadedSolution).where(UploadedSolution.id == upload_id).with_for_update())
    if not row or row.user_id != user.id:
        raise HTTPException(404, 'Upload not found.')
    if row.confirmed:
        raise HTTPException(409, 'This transcription has already been confirmed.')
    result = analyze(data.steps)
    for i, equation in enumerate(data.steps):
        if len(equation) > 200:
            raise MathError('Each step must be at most 200 characters.')
        db.add(ExtractedSolutionStep(upload_id=row.id, position=i, equation=equation))
    row.confirmed = True
    db.add(SolutionFeedback(user_id=user.id, upload_id=row.id, result=result))
    db.commit()
    return result


@app.put(prefix + '/me', response_model=dto.UserOut)
def update_profile(data: dto.ProfileUpdate, user: Student, db: DB):
    name = data.name.strip()
    if not name:
        raise HTTPException(422, 'Enter a name containing at least one non-space character.')
    user.name = name
    db.commit()
    return {'id': user.id, 'name': user.name, 'email': user.email}


@app.get(prefix + '/sessions', response_model=list[dto.SessionOut])
def list_sessions(user: Student, db: DB):
    return list(db.scalars(select(LearningSession).where(LearningSession.user_id == user.id)))


@app.post(prefix + '/sessions', response_model=dto.SessionOut)
def start_session(data: dto.SessionCreate, user: Student, db: DB):
    if not db.get(Lesson, data.lesson_id):
        raise HTTPException(404, 'Lesson not found.')
    row = db.scalar(select(LearningSession).where(LearningSession.user_id == user.id, LearningSession.lesson_id == data.lesson_id))
    if not row:
        row = LearningSession(user_id=user.id, lesson_id=data.lesson_id)
        db.add(row)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            row = db.scalar(select(LearningSession).where(LearningSession.user_id == user.id, LearningSession.lesson_id == data.lesson_id))
    return row


@app.get(prefix + '/recommendations')
def recommendations(user: Student, db: DB):
    row = db.get(LearningRecommendation, user.id)
    return {'algorithm': 'deterministic rules', 'reason': row.reason if row else 'Start with The art of balance, then try a short quiz.'}


@app.get(prefix + '/tutor/status')
def tutor_status(user: Student):
    configured = settings.ai_provider == 'meta' and bool(settings.model_api_key)
    return {'provider': settings.ai_provider, 'configured': configured, 'live_verified': False, 'message': 'Meta is configured; requests may still fail if the account lacks model access.' if configured else 'Local development mode. Set AI_PROVIDER=meta and MODEL_API_KEY on the backend to enable Meta text and vision.'}
