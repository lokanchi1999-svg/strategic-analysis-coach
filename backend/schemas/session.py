from enum import StrEnum
from typing import Any
from pydantic import BaseModel, ConfigDict, Field, model_validator
from .message import Message
from .model import ModelCredentials, ModelProfile
from .evaluation import EvaluationResult, PublicEvaluationResult, QuestionAction

class SessionMode(StrEnum):
    GUIDED = "guided"
    FREE = "free"

class SessionPhase(StrEnum):
    SETUP = "SETUP"
    FRAMEWORK_SELECTION = "FRAMEWORK_SELECTION"
    ANALYSIS = "ANALYSIS"
    INTEGRATION = "INTEGRATION"
    REFLECTION = "REFLECTION"
    COMPLETE = "COMPLETE"

class SelectionStatus(StrEnum):
    NOT_STARTED = "NOT_STARTED"
    NEEDS_STUDENT_CHOICE = "NEEDS_STUDENT_CHOICE"
    CONFIRMED = "CONFIRMED"

class FrameworkCandidate(BaseModel):
    skill_id: str
    name: str
    reason: str
    fit: str | None = None

class AnalysisIntent(BaseModel):
    primary_question: str | None = None
    unit_of_analysis: str | None = None
    perspective: str | None = None

class FrameworkSelectionResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    analysis_intent: AnalysisIntent = Field(default_factory=AnalysisIntent)
    candidates: list[FrameworkCandidate] = Field(default_factory=list)
    selection_status: SelectionStatus = SelectionStatus.NOT_STARTED
    selected_skill: str | None = None
    student_visible_response: str = ""

class FrameworkSelectionState(BaseModel):
    candidates: list[FrameworkCandidate] = Field(default_factory=list)
    status: SelectionStatus = SelectionStatus.NOT_STARTED

class SessionState(BaseModel):
    model_config = ConfigDict(extra="forbid")
    session_id: str
    mode: SessionMode
    phase: SessionPhase = SessionPhase.SETUP
    case_code: str | None = None
    active_skill: str | None = None
    current_dimension: str | None = None
    current_depth: int = 0
    coverage: dict[str, Any] = Field(default_factory=dict)
    student_goal: str | None = None
    source_material: str | None = Field(default=None, exclude=True)
    framework_selection: FrameworkSelectionState = Field(default_factory=FrameworkSelectionState)
    last_evaluation: EvaluationResult | None = Field(default=None, exclude=True)
    last_question_action: QuestionAction | None = None
    turn_count: int = 0
    messages: list[Message] = Field(default_factory=list)

class SessionCreate(BaseModel):
    mode: SessionMode
    case_code: str | None = None
    material: str | None = Field(default=None, max_length=100_000)
    student_goal: str | None = Field(default=None, max_length=2_000)
    model_profile: ModelProfile | None = None
    credentials: ModelCredentials | None = None

    @model_validator(mode="after")
    def validate_mode_inputs(self):
        if self.mode == SessionMode.GUIDED and not self.case_code:
            raise ValueError("case_code is required for guided mode")
        if self.mode == SessionMode.FREE and not self.material:
            raise ValueError("material is required for free mode")
        return self

class StudentMessageRequest(BaseModel):
    content: str = Field(min_length=1, max_length=50_000)

class CoachTurnResponse(BaseModel):
    session: "PublicSessionView"
    action: QuestionAction
    student_visible_response: str

class PublicSessionView(BaseModel):
    """Explicit allow-list for state that may cross the API boundary."""
    session_id: str
    mode: SessionMode
    phase: SessionPhase
    case_code: str | None = None
    active_skill: str | None = None
    current_dimension: str | None = None
    current_depth: int = 0
    coverage: dict[str, Any] = Field(default_factory=dict)
    student_goal: str | None = None
    framework_selection: FrameworkSelectionState
    last_evaluation: PublicEvaluationResult | None = None
    last_question_action: QuestionAction | None = None
    turn_count: int = 0
    messages: list[Message] = Field(default_factory=list)

    @classmethod
    def from_internal(cls, state: SessionState) -> "PublicSessionView":
        payload = state.model_dump(exclude={"source_material", "last_evaluation"})
        payload["last_evaluation"] = PublicEvaluationResult.from_internal(state.last_evaluation)
        return cls.model_validate(payload)
