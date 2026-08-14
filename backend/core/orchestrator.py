from ..model_gateway.credentials import SessionCredentialVault
from ..model_gateway.registry import create_gateway
from ..schemas.message import MessageRole
from ..schemas.model import ModelProfile
from ..schemas.evaluation import QuestionAction
from ..schemas.session import CoachTurnResponse, PublicSessionView, SelectionStatus, SessionPhase
from ..storage.case_store import FileCaseStore
from ..storage.session_store import SessionStore
from ..storage.skill_store import FileSkillStore, SkillNotFoundError
from .context_builder import ContextBuilder
from .evaluator import Evaluator
from .question_generator import QuestionGenerator
from .session_controller import SessionController
from .state_transition import StateTransition

class Orchestrator:
    def __init__(self, sessions: SessionStore, cases: FileCaseStore, skills: FileSkillStore, vault: SessionCredentialVault, context_builder: ContextBuilder):
        self.sessions, self.cases, self.skills, self.vault = sessions, cases, skills, vault
        self.context_builder, self.controller = context_builder, SessionController(sessions, cases)
        self.evaluator, self.transition, self.questions = Evaluator(), StateTransition(), QuestionGenerator()
    async def handle(self, session_id: str, content: str) -> CoachTurnResponse:
        state = await self.sessions.get(session_id)
        await self.controller.append_message(state, MessageRole.STUDENT, content)
        if state.phase == SessionPhase.FRAMEWORK_SELECTION:
            selected = next((c for c in state.framework_selection.candidates if c.skill_id.lower() in content.lower()), None)
            if not selected:
                reply = "请选择一个候选框架，并说明它如何匹配你的分析问题与分析单位。当前可选：" + "、".join(c.name for c in state.framework_selection.candidates)
                await self.controller.append_message(state, MessageRole.COACH, reply)
                return CoachTurnResponse(session=PublicSessionView.from_internal(state), action=QuestionAction.ASK_CLARIFICATION, student_visible_response=reply)
            try: await self.skills.load(selected.skill_id)
            except SkillNotFoundError:
                reply = f"{selected.name} 的分析 Skill 尚未安装，请选择当前可用的 five_forces。"
                await self.controller.append_message(state, MessageRole.COACH, reply)
                return CoachTurnResponse(session=PublicSessionView.from_internal(state), action=QuestionAction.ASK_CLARIFICATION, student_visible_response=reply)
            state.active_skill, state.phase = selected.skill_id, SessionPhase.ANALYSIS
            state.framework_selection.status = SelectionStatus.CONFIRMED
        skill = await self.skills.load(state.active_skill) if state.active_skill else None
        hidden = {}; instructor_override = {}
        if state.case_code:
            case = await self.cases.load(state.case_code); hidden = case.teacher_annotations
        context_args=dict(state=state,skill=skill,current_message=content,instructor_override=instructor_override,teacher_annotations=hidden)
        evaluator_context=self.context_builder.build_evaluator_context(**context_args)
        question_context=self.context_builder.build_question_generator_context(**context_args)
        stored = await self.vault.get(session_id)
        profile, credentials = stored if stored else (ModelProfile(), None)
        gateway = create_gateway(profile, credentials)
        evaluation = await self.evaluator.evaluate(gateway, evaluator_context)
        state = self.transition.apply(state, evaluation)
        question = await self.questions.generate(gateway, state, evaluation, question_context)
        state.last_question_action = question.action
        await self.controller.append_message(state, MessageRole.COACH, question.student_visible_response)
        return CoachTurnResponse(session=PublicSessionView.from_internal(state), action=question.action, student_visible_response=question.student_visible_response)
