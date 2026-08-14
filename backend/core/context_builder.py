import json
from pathlib import Path
from typing import Any
from ..schemas.session import SessionMode, SessionState

class ContextBuilder:
    def __init__(self,core_policy:Path): self.core_policy=core_policy
    def _shared_payload(self,*,state,skill,current_message,instructor_override=None,teacher_annotations=None):
        context={"session":state.model_dump(mode="json",exclude={"messages","source_material","last_evaluation"}),"skill":skill,"instructor_override":instructor_override or {},"recent_conversation":[m.model_dump(mode="json") for m in state.messages[-8:]],"student_message":current_message}
        if state.mode==SessionMode.GUIDED: context["teacher_annotations"]=teacher_annotations or {}
        return json.dumps(context,ensure_ascii=False,default=str)
    def build_evaluator_context(self,**kwargs):
        """Shared facts only; Evaluator adds its own non-conversational contract."""
        return [{"role":"user","content":self._shared_payload(**kwargs)}]
    def build_question_generator_context(self,**kwargs):
        return [{"role":"system","content":self.core_policy.read_text("utf-8")},{"role":"user","content":self._shared_payload(**kwargs)}]
    def build(self,**kwargs):
        """Backward-compatible alias for student-facing context."""
        return self.build_question_generator_context(**kwargs)
