"""Frozen v0.2 evaluator and question-generation contracts."""
from enum import StrEnum
from pydantic import BaseModel, ConfigDict, Field

class QualityRating(StrEnum):
    MISSING="missing"; WEAK="weak"; PARTIAL="partial"; SUFFICIENT="sufficient"; STRONG="strong"; UNKNOWN="unknown"

class FactAccuracy(StrEnum):
    SUPPORTED="supported"; CONTRADICTED="contradicted"; MIXED="mixed"; UNKNOWN="unknown"; NOT_APPLICABLE="not_applicable"

class QuestionAction(StrEnum):
    ASK_CLARIFICATION="ASK_CLARIFICATION"; PROBE_CLAIM="PROBE_CLAIM"; PROBE_EVIDENCE="PROBE_EVIDENCE"
    PROBE_MECHANISM="PROBE_MECHANISM"; CHECK_CASE_FACT="CHECK_CASE_FACT"; CHALLENGE_ASSUMPTION="CHALLENGE_ASSUMPTION"
    ASK_COUNTEREXAMPLE="ASK_COUNTEREXAMPLE"; TEST_BOUNDARY="TEST_BOUNDARY"; COMPARE_ALTERNATIVE="COMPARE_ALTERNATIVE"
    CONNECT_DIMENSIONS="CONNECT_DIMENSIONS"; ASK_SYNTHESIS="ASK_SYNTHESIS"; ADVANCE_DIMENSION="ADVANCE_DIMENSION"

class EvaluationResult(BaseModel):
    model_config=ConfigDict(extra="forbid")
    skill_id: str=Field(pattern=r"^[a-z][a-z0-9_]*$")
    dimension: str|None=None
    depth_level: int|None=Field(default=None,ge=0)
    claim_quality: QualityRating|None=None
    evidence_quality: QualityRating|None=None
    mechanism_quality: QualityRating|None=None
    integration_quality: QualityRating|None=None
    case_fact_accuracy: FactAccuracy|None=None
    missing_fact_ids: list[str]=Field(default_factory=list)
    misconceptions: list[str]=Field(default_factory=list)
    advance: bool=False
    recommended_action: QuestionAction|None=None
    confidence: float|None=Field(default=None,ge=0,le=1)
    notes: str|None=None

class PublicEvaluationResult(BaseModel):
    """Student-safe evaluator view; internal notes are deliberately absent."""
    skill_id: str
    dimension: str|None=None
    depth_level: int|None=None
    claim_quality: QualityRating|None=None
    evidence_quality: QualityRating|None=None
    mechanism_quality: QualityRating|None=None
    integration_quality: QualityRating|None=None
    case_fact_accuracy: FactAccuracy|None=None
    missing_fact_ids: list[str]=Field(default_factory=list)
    misconceptions: list[str]=Field(default_factory=list)
    advance: bool=False
    recommended_action: QuestionAction|None=None
    confidence: float|None=None
    @classmethod
    def from_internal(cls,value: EvaluationResult|None):
        return None if value is None else cls.model_validate(value.model_dump(exclude={"notes"}))

class QuestionGenerationResult(BaseModel):
    model_config=ConfigDict(extra="forbid")
    action: QuestionAction
    student_visible_response: str=Field(min_length=1)
    process_feedback: str|None=None

QuestionResult=QuestionGenerationResult
