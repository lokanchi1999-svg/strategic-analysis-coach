from pathlib import Path
import pytest
from backend.core.context_builder import ContextBuilder
from backend.core.orchestrator import Orchestrator
from backend.core.state_transition import StateTransition
from backend.model_gateway.base import GatewayError, ModelGateway
from backend.model_gateway.credentials import SessionCredentialVault
from backend.schemas.evaluation import EvaluationResult
from backend.schemas.session import SessionCreate
from backend.storage.case_store import FileCaseStore
from backend.storage.session_store import InMemorySessionStore
from backend.storage.skill_store import FileSkillStore

ROOT=Path(__file__).parents[1]
def test_state_transition_records_evaluation_but_does_not_invent_next_dimension():
    from backend.schemas.session import SessionState,SessionMode
    state=SessionState(session_id="x",mode=SessionMode.GUIDED,current_dimension="supplier_power",current_depth=1)
    result=StateTransition().apply(state,EvaluationResult(skill_id="five_forces",dimension="supplier_power",depth_level=1,advance=False,recommended_action="PROBE_EVIDENCE"))
    assert result.current_dimension=="supplier_power" and result.current_depth==1 and result.last_evaluation is not None
    advanced=StateTransition().apply(result,EvaluationResult(skill_id="five_forces",dimension="supplier_power",depth_level=2,advance=True,recommended_action="ADVANCE_DIMENSION"))
    assert advanced.current_depth==2 and advanced.coverage["supplier_power"]["advance"] is True

class FailingQuestions:
    async def generate(self,*args,**kwargs): raise GatewayError("TIMEOUT","Question generation timed out")

@pytest.mark.asyncio
async def test_question_generator_failure_does_not_persist_transition():
    sessions=InMemorySessionStore(); cases=FileCaseStore(ROOT/"cases"); skills=FileSkillStore(ROOT/"skills")
    orchestrator=Orchestrator(sessions,cases,skills,SessionCredentialVault(),ContextBuilder(ROOT/"coach_core"/"core_policy.md"))
    state=await orchestrator.controller.create(SessionCreate(mode="guided",case_code="SAMPLE-CASE-01")); orchestrator.questions=FailingQuestions()
    with pytest.raises(GatewayError,match="timed out"): await orchestrator.handle(state.session_id,"claim")
    stored=await sessions.get(state.session_id)
    assert stored.current_depth==0 and stored.last_evaluation is None and stored.turn_count==1

class TimeoutGateway(ModelGateway):
    async def generate(self,**kwargs): raise GatewayError("TIMEOUT","Model request timed out")

@pytest.mark.asyncio
async def test_timeout_is_typed_application_error():
    from backend.core.evaluator import Evaluator
    with pytest.raises(GatewayError) as caught: await Evaluator().evaluate(TimeoutGateway(),[])
    assert caught.value.error_type=="TIMEOUT"
