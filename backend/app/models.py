import uuid
import time
from sqlalchemy import String, ForeignKey, JSON, UniqueConstraint, BigInteger
from sqlalchemy.orm import Mapped, mapped_column
from .db import Base


def uid():
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = 'users'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    email: Mapped[str] = mapped_column(String(254), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(80))
    password_hash: Mapped[str] = mapped_column(String(255))


class UserSettings(Base):
    __tablename__ = 'user_settings'
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id'), primary_key=True)
    muted: Mapped[bool] = mapped_column(default=False)
    voice: Mapped[str] = mapped_column(String(200), default='')


class RefreshToken(Base):
    __tablename__ = 'refresh_tokens'
    digest: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id'), index=True)
    family: Mapped[str] = mapped_column(String(36), index=True)
    expires: Mapped[int]
    revoked: Mapped[bool] = mapped_column(default=False)


class Topic(Base):
    __tablename__ = 'topics'
    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    title: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(String(500))


class Lesson(Base):
    __tablename__ = 'lessons'
    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    topic_id: Mapped[str] = mapped_column(ForeignKey('topics.id'))
    title: Mapped[str] = mapped_column(String(100))
    equation: Mapped[str] = mapped_column(String(200))


class LessonStep(Base):
    __tablename__ = 'lesson_steps'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    lesson_id: Mapped[str] = mapped_column(ForeignKey('lessons.id'), index=True)
    position: Mapped[int]
    content: Mapped[dict] = mapped_column(JSON)


class LearningSession(Base):
    __tablename__ = 'learning_sessions'
    __table_args__ = (UniqueConstraint('user_id', 'lesson_id'),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id'), index=True)
    lesson_id: Mapped[str] = mapped_column(ForeignKey('lessons.id'))
    completed: Mapped[bool] = mapped_column(default=False)


class TutorMessage(Base):
    __tablename__ = 'tutor_messages'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id'), index=True)
    question: Mapped[str] = mapped_column(String(2000))
    answer: Mapped[str] = mapped_column(String(4000))


class QuizQuestion(Base):
    __tablename__ = 'quiz_questions'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id'), index=True)
    topic_id: Mapped[str] = mapped_column(ForeignKey('topics.id'))
    equation: Mapped[str] = mapped_column(String(200))
    difficulty: Mapped[int]
    hinted: Mapped[bool] = mapped_column(default=False)


class QuizAttempt(Base):
    __tablename__ = 'quiz_attempts'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id'), index=True)
    question_id: Mapped[str] = mapped_column(ForeignKey('quiz_questions.id'), unique=True)
    correct: Mapped[bool]
    hinted: Mapped[bool]
    created: Mapped[int] = mapped_column(default=lambda: int(time.time()))
    submitted_at: Mapped[int] = mapped_column(BigInteger, default=time.time_ns, index=True)


class StudentAnswer(Base):
    __tablename__ = 'student_answers'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    attempt_id: Mapped[str] = mapped_column(ForeignKey('quiz_attempts.id'), unique=True)
    answer: Mapped[str] = mapped_column(String(200))


class UploadedSolution(Base):
    __tablename__ = 'uploaded_solutions'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id'), index=True)
    filename: Mapped[str] = mapped_column(String(255))
    width: Mapped[int]
    height: Mapped[int]
    confirmed: Mapped[bool] = mapped_column(default=False)


class ExtractedSolutionStep(Base):
    __tablename__ = 'extracted_solution_steps'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    upload_id: Mapped[str] = mapped_column(ForeignKey('uploaded_solutions.id'), index=True)
    position: Mapped[int]
    equation: Mapped[str] = mapped_column(String(200))


class SolutionFeedback(Base):
    __tablename__ = 'solution_feedback'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id'), index=True)
    upload_id: Mapped[str | None] = mapped_column(ForeignKey('uploaded_solutions.id'), nullable=True)
    result: Mapped[dict] = mapped_column(JSON)


class TopicMastery(Base):
    __tablename__ = 'topic_mastery'
    __table_args__ = (UniqueConstraint('user_id', 'topic_id'),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id'), index=True)
    topic_id: Mapped[str] = mapped_column(ForeignKey('topics.id'))
    difficulty: Mapped[int] = mapped_column(default=1)
    accuracy: Mapped[float] = mapped_column(default=0)


class LearningRecommendation(Base):
    __tablename__ = 'learning_recommendations'
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id'), primary_key=True)
    reason: Mapped[str] = mapped_column(String(500))
