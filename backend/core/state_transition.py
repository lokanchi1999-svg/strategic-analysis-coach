from ..schemas.evaluation import EvaluationResult
from ..schemas.session import SessionState

class StateTransition:
    def apply(self, state: SessionState, evaluation: EvaluationResult) -> SessionState:
        updated = state.model_copy(deep=True)
        updated.last_evaluation = evaluation
        updated.last_question_action = evaluation.recommended_action
        if evaluation.dimension: updated.current_dimension = evaluation.dimension
        if evaluation.depth_level is not None: updated.current_depth = evaluation.depth_level
        if evaluation.dimension:
            updated.coverage[evaluation.dimension] = {"depth": evaluation.depth_level, "advance": evaluation.advance}
        return updated
