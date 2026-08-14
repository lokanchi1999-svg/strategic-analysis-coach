import pytest
from pydantic import ValidationError
from backend.schemas.evaluation import EvaluationResult, FactAccuracy, QualityRating, QuestionAction, QuestionGenerationResult
from backend.schemas.session import FrameworkSelectionResult, PublicSessionView, SessionMode, SessionState
from backend.schemas.skill import SkillManifest

def test_frozen_evaluation_and_question_contracts():
    result=EvaluationResult(skill_id="five_forces",claim_quality="sufficient",case_fact_accuracy="supported",recommended_action="PROBE_MECHANISM",notes="internal")
    assert result.claim_quality is QualityRating.SUFFICIENT
    assert result.case_fact_accuracy is FactAccuracy.SUPPORTED
    assert QuestionGenerationResult(action="PROBE_MECHANISM",student_visible_response="Why?").action is QuestionAction.PROBE_MECHANISM
    with pytest.raises(ValidationError): EvaluationResult(skill_id="five_forces",claim_quality="excellent")

def test_public_session_excludes_internal_evaluation_notes():
    state=SessionState(session_id="x",mode=SessionMode.GUIDED,last_evaluation=EvaluationResult(skill_id="five_forces",notes="teacher_reference secret"))
    payload=PublicSessionView.from_internal(state).model_dump(mode="json")
    assert "notes" not in payload["last_evaluation"] and "teacher_reference" not in str(payload)

def test_manifest_contract_is_strict():
    with pytest.raises(ValidationError): SkillManifest.model_validate({"id":"bad-id","type":"analysis","version":"v1","name":{"en":"X","zh":"X"},"dimensions":[],"depth_levels":[]})

def test_framework_selection_result_contract():
    result=FrameworkSelectionResult(selection_status="NEEDS_STUDENT_CHOICE",student_visible_response="Choose")
    assert result.selection_status.value=="NEEDS_STUDENT_CHOICE"
