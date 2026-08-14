from uuid import uuid4
from ..schemas.message import Message, MessageRole
from ..schemas.session import FrameworkCandidate, SelectionStatus, SessionCreate, SessionMode, SessionPhase, SessionState
from ..storage.case_store import FileCaseStore
from ..storage.session_store import SessionStore

class SessionController:
    def __init__(self, sessions: SessionStore, cases: FileCaseStore): self.sessions, self.cases = sessions, cases
    async def create(self, request: SessionCreate) -> SessionState:
        state = SessionState(session_id=str(uuid4()), mode=request.mode, student_goal=request.student_goal)
        if request.mode == SessionMode.GUIDED:
            case = await self.cases.load(request.case_code or "")
            state.case_code, state.active_skill, state.phase = case.manifest.case_code, case.manifest.skill_id, SessionPhase.ANALYSIS
        else:
            state.source_material, state.phase = request.material, SessionPhase.FRAMEWORK_SELECTION
            state.framework_selection.status = SelectionStatus.NEEDS_STUDENT_CHOICE
            state.framework_selection.candidates = [
                FrameworkCandidate(skill_id="five_forces", name="波特五力", reason="适合分析行业结构与竞争压力。"),
                FrameworkCandidate(skill_id="swot", name="SWOT（元数据占位）", reason="适合先组织内外部因素；对应分析 Skill 尚待添加。"),
            ]
        await self.sessions.save(state); return state
    async def append_message(self, state: SessionState, role: MessageRole, content: str):
        state.messages.append(Message(role=role, content=content))
        if role == MessageRole.STUDENT: state.turn_count += 1
        await self.sessions.save(state)

