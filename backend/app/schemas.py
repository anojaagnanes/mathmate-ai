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
    verify_only: bool = False


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


class GeometryDiagram(BaseModel):
    shape: Literal['rectangle', 'triangle', 'right_triangle', 'circle']
    labels: list[str]
    caption: str


class SolutionOut(BaseModel):
    diagram: GeometryDiagram | None = None
    kind: Literal['unique', 'none', 'infinite', 'multiple', 'expression', 'underdetermined', 'parametric', 'system', 'inequality', 'calculus', 'linear_algebra']
    domain_conditions: list[str] = Field(default_factory=list)
    assignments: dict[str, str] = Field(default_factory=dict)
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
    cheer: str | None = None
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


class DocumentPageOut(BaseModel):
    page: int
    text: str


class DocumentTextOut(BaseModel):
    text: str
    mode: Literal['pdf_text', 'manual']
    pages: int
    message: str
    page_text: list[DocumentPageOut] = Field(default_factory=list)
    unread_pages: list[int] = Field(default_factory=list)


class ConstructionStepOut(BaseModel):
    en: str
    ta: str
    why_en: str
    why_ta: str


class ConstructionCheckOut(BaseModel):
    en: str
    ta: str


class ConstructionGuideOut(BaseModel):
    label: str
    matched: bool = True
    kind: str
    source: str = ''
    title_en: str
    title_ta: str
    given: str = ''
    steps: list[ConstructionStepOut]
    checks: list[ConstructionCheckOut] = Field(default_factory=list)
    diagram: dict[str, str] = Field(default_factory=dict)


class QuestionInputOut(BaseModel):
    feedback: FeedbackOut | None = None
    suggested_variable: str | None = None
    suggested_input: str | None = None
    question_type: str | None = None
    document: DocumentTextOut | None = None
    proposed_math: str | None = None
    assumptions: list[str] = Field(default_factory=list)
    route: Literal['solver', 'interpretation', 'image', 'document', 'working', 'construction']
    status: Literal['solved', 'unsupported', 'review_required', 'manual_required']
    message: str
    question: str
    solution: SolutionOut | None = None
    upload: UploadOut | None = None
    guides: list[ConstructionGuideOut] = Field(default_factory=list)


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


class FunctionGraph(BaseModel):
    expression: str = Field(min_length=1, max_length=200)
    minimum: float = Field(default=-5, ge=-10, le=10, allow_inf_nan=False)
    maximum: float = Field(default=5, ge=-10, le=10, allow_inf_nan=False)


class FunctionGraphOut(BaseModel):
    segments: list[list[dict[str, float]]]
    latex: str
    domain_conditions: list[str]
    note: str


class MiaSessionCreate(BaseModel):
    language: Literal['en', 'ta'] = 'en'
    mode: Literal['classroom', 'whiteboard'] = 'classroom'
    question: str = Field(default='', max_length=2000)


class MiaSessionOut(BaseModel):
    id: str
    language: str
    mode: str
    step_index: int
    question: str
    pace: str
    method: str


class MiaTurnIn(BaseModel):
    session_id: str = Field(min_length=1, max_length=36)
    message: str = Field(min_length=1, max_length=2000)
    equation: str = Field(default='', max_length=2000)
    language: Literal['en', 'ta'] | None = None
    slow: bool = False
    method: Literal['default', 'alternative', 'visual'] | None = None
    step_index: int | None = None
    image_base64: str | None = Field(default=None, max_length=7000000)
    image_mime: Literal['image/png', 'image/jpeg', 'image/webp'] | None = None
    pdf_base64: str | None = Field(default=None, max_length=7000000)
    context: str = Field(default='', max_length=80)


class WhiteboardStep(BaseModel):
    equation: str
    latex: str | None = None
    diagram: GeometryDiagram | None = None


class MiaTurnOut(BaseModel):
    reply: str
    language: str
    mode: str
    intent: str
    plan: list[str]
    verified_math: SolutionOut | None = None
    whiteboard: list[WhiteboardStep] = Field(default_factory=list)
    followups: list[str] = Field(default_factory=list)
    practice: dict | None = None
    real_world: str | None = None
    voice_rate: float
    provider_mode: str
    trace: list[dict] = Field(default_factory=list)


class MiaTurnHistory(BaseModel):
    role: str
    message: str
    language: str
    step_index: int


class MiaHistoryOut(BaseModel):
    session: MiaSessionOut
    turns: list[MiaTurnHistory]


class MiaVoiceOut(BaseModel):
    tts: Literal['browser']
    stt: Literal['browser_optional', 'disabled']
    languages: list[str]
    rates: dict[str, float]
    message: str


class MissionAnswer(BaseModel):
    answer: str = Field(min_length=1, max_length=200)


class MissionDrillOut(BaseModel):
    number: int
    equation: str
    hint: str = ''
    difficulty: int
    kind: str = 'value'
    steps: list[str] = Field(default_factory=list)


class MissionOut(BaseModel):
    id: str
    goal: str
    briefing: str | None = None
    topic: str
    error: str | None = None
    state: str
    difficulty: int
    drills_done: int
    consecutive: int
    exit_wins: int
    max_drills: int
    example: dict | None = None
    current: MissionDrillOut | None = None
    trace: list[str] = Field(default_factory=list)
    verdict: dict | None = None


class MissionTurnOut(BaseModel):
    cheer: str | None = None
    correct: bool
    message: str
    consecutive: int
    drills_done: int
    difficulty: int
    state: str
    current: MissionDrillOut | None = None
    trace: list[str] = Field(default_factory=list)
    verdict: dict | None = None


class JourneyIslandOut(BaseModel):
    key: str
    title: str
    subtitle: str
    topic: str
    state: str
    gems: int
    asked: int


class JourneyDrillOut(BaseModel):
    number: int
    equation: str
    hint: str = ''
    difficulty: int
    kind: str = 'value'
    prompt: str = ''
    steps: list[str] = Field(default_factory=list)
    lifelines: list[str] = Field(default_factory=list)


class JourneyOut(BaseModel):
    story: str | None = None
    id: str
    state: str
    island_index: int
    islands: list[JourneyIslandOut] = Field(default_factory=list)
    gems_needed: int
    questions_done: int
    correct_count: int
    assists: int
    current: JourneyDrillOut | None = None
    trace: list[str] = Field(default_factory=list)
    verdict: dict | None = None


class JourneyTurnOut(BaseModel):
    story: str | None = None
    advanced: bool = True
    correct: bool
    message: str
    event: str | None = None
    state: str
    island_index: int
    islands: list[JourneyIslandOut] = Field(default_factory=list)
    gems_needed: int
    questions_done: int
    correct_count: int
    assists: int
    current: JourneyDrillOut | None = None
    trace: list[str] = Field(default_factory=list)
    verdict: dict | None = None


class JourneyLifelineIn(BaseModel):
    kind: str = Field(min_length=1, max_length=20)


class JourneyLifelineOut(BaseModel):
    kind: str
    text: str
    step: dict | None = None
    steps: list[dict] = Field(default_factory=list)
    answer: str | None = None
    revealed: bool = False
