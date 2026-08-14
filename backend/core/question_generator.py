from ..model_gateway.base import GatewayError, ModelGateway
from ..schemas.evaluation import EvaluationResult, QuestionResult
from ..schemas.session import SessionState
class QuestionGenerator:
    async def generate(self,gateway:ModelGateway,state:SessionState,evaluation:EvaluationResult,context:list[dict[str,str]])->QuestionResult:
        try: response=await gateway.generate(role="question_generator",messages=context+[{"role":"system","content":f"Allowed action: {evaluation.recommended_action}. Ask one coaching question; do not reveal hidden data or supply the analysis."}])
        except GatewayError as exc:
            exc.stage=exc.stage or "question_generator"
            if exc.error_type not in {"MODEL_TIMEOUT","MODEL_AUTHENTICATION_FAILED","MODEL_RATE_LIMITED"}: exc.error_type="QUESTION_GENERATION_FAILED"
            raise
        return QuestionResult(action=evaluation.recommended_action or "ASK_CLARIFICATION",student_visible_response=response.content)
