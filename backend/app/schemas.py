from typing import Annotated, Literal
from pydantic import BaseModel, EmailStr, Field, ConfigDict, StringConstraints


class Register(BaseModel):
    email: EmailStr
    password: str = Field(min_length=10, max_length=128)
    name: str = Field(min_length=1, max_length=80)


class Login(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class Equation(BaseModel):
    equation: str = Field(min_length=1, max_length=200)
    variable: str | None = Field(default=None, max_length=5)


class Steps(BaseModel):
    steps: list[Annotated[str, StringConstraints(strip_whitespace=True, min_length=3, max_length=200)]] = Field(min_length=1, max_length=30)


class Answer(BaseModel):
    answer: str = Field(min_length=1, max_length=200)


class Chat(Equation):
    message: str = Field(min_length=1, max_length=2000)


class Preferences(BaseModel):
    muted: bool = False
    voice: str = Field(default='', max_length=200)


class Graph(BaseModel):
    slope: float = Field(ge=-20, le=20, allow_inf_nan=False)
    intercept: float = Field(ge=-20, le=20, allow_inf_nan=False)


class UserOut(BaseModel):
    id: str
    name: str
    email: EmailStr


class AuthOut(BaseModel):
    access_token: str
    token_type: Literal['bearer']
    user: UserOut


class SolutionStep(BaseModel):
    equation: str
    explanation: str
    latex: str | None = None


class SolutionOut(BaseModel):
    kind: Literal['unique', 'none', 'infinite', 'multiple', 'expression', 'underdetermined', 'parametric']
    solutions: list[str] = Field(default_factory=list)
    variable: str | None = None
    variables: list[str] = Field(default_factory=list)
    topic: str = 'Linear equation'
    domain: str = 'real'
    solution: str | None
    steps: list[SolutionStep]
    verified: bool
    latex: str


class FeedbackOut(BaseModel):
    valid: bool
    first_incorrect_step: int | None
    message: str
    error_code: str | None = None
    corrected: SolutionOut


class LessonSummary(BaseModel):
    id: str
    title: str
    equation: str


class LessonOut(LessonSummary):
    solution: SolutionOut


class TopicOut(BaseModel):
    id: str
    title: str
    description: str
    lessons: list[LessonSummary]


class QuestionOut(BaseModel):
    id: str
    equation: str
    difficulty: int
    prompt: str


class SubmissionOut(BaseModel):
    correct: bool
    solution: SolutionOut
    recommendation: str
    difficulty: int


class ChatOut(BaseModel):
    message: str
    mode: str
    verified_math: SolutionOut


class UploadOut(BaseModel):
    id: str
    steps: list[str]
    mode: str
    message: str


class SessionCreate(BaseModel):
    lesson_id: str = Field(min_length=1, max_length=40)


class SessionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    lesson_id: str
    completed: bool


class ProfileUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=80)


class MasteryOut(BaseModel):
    topic: str
    accuracy: float
    difficulty: int


class HistoryOut(BaseModel):
    number: int
    correct: int
    hinted: bool


class ProgressOut(BaseModel):
    attempts: int
    correct: int
    hints: int
    completed_lessons: list[str]
    recommendation: str
    mastery: list[MasteryOut]
    history: list[HistoryOut]
    reviews: list[FeedbackOut]
    common_errors: int
    error_categories: dict[str, int]


class GraphOut(BaseModel):
    points: list[dict[str, float]]
    x_intercept: float | None
