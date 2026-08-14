from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field
from ..schemas.evaluation import QuestionAction

class EvalInput(BaseModel):
    model_config=ConfigDict(extra="allow")
    mode: str|None=None; skill_id: str|None=None; dimension: str|None=None; student_response: str=Field(min_length=1)
class EvalExpected(BaseModel):
    model_config=ConfigDict(extra="allow")
    depth_level: int|None=None; advance: bool|None=None; recommended_action: QuestionAction|None=None
    selected_skill: str|None=None; forbidden_phrases: list[str]=Field(default_factory=list)
class EvalCase(BaseModel):
    model_config=ConfigDict(extra="forbid")
    id: str; category: str; input: EvalInput; expected: EvalExpected; notes: str
class Metric(BaseModel): passed:int=0; total:int=0
class EvalFailure(BaseModel): case_id:str; field:str; expected:Any=None; actual:Any=None
class EvalReport(BaseModel):
    suite:str; cases:int; metrics:dict[str,Metric]; failures:list[EvalFailure]=Field(default_factory=list); placeholder:bool=True
