import json, logging
from pydantic import ValidationError
from ..model_gateway.base import GatewayError, ModelGateway
from ..schemas.evaluation import EvaluationResult

logger=logging.getLogger("coach.evaluator")
EXAMPLE={"skill_id":"five_forces","dimension":"supplier_power","depth_level":1,"claim_quality":"partial","evidence_quality":"missing","mechanism_quality":"missing","integration_quality":"missing","case_fact_accuracy":"unknown","missing_fact_ids":[],"misconceptions":[],"advance":False,"recommended_action":"PROBE_EVIDENCE","confidence":0.8,"notes":None}

class EvaluationError(RuntimeError):
    def __init__(self,error_type:str,message:str,*,stage="evaluator"):
        super().__init__(message); self.error_type=error_type; self.stage=stage

class Evaluator:
    def _instruction(self,schema):
        return """You are an internal evaluation component. You are NOT the student-facing coach.
Do not ask questions or output conversational prose. Do not output role, content, type, or coach_message fields.
Classify only the student's current response. Return exactly one JSON object and nothing else: no Markdown, code fences, or explanation.
The object must match this JSON Schema:\n"""+json.dumps(schema,ensure_ascii=False)+"\nMinimal structure example (not a teaching rubric):\n"+json.dumps(EXAMPLE,ensure_ascii=False)
    def _repair_instruction(self,raw,errors,schema):
        return "Your previous response did not match EvaluationResult. Return a corrected JSON object only. Do not produce a student-facing coach message. Do not add role/content/type. Do not explain or change substantive judgment except as required by the schema.\nValidation errors:\n"+json.dumps(errors,ensure_ascii=False)+"\nSchema:\n"+json.dumps(schema,ensure_ascii=False)+"\nPrevious output:\n"+raw[:8000]
    async def evaluate(self,gateway:ModelGateway,messages:list[dict[str,str]])->EvaluationResult:
        schema=EvaluationResult.model_json_schema(); evaluator_messages=[{"role":"system","content":self._instruction(schema)}]+[m for m in messages if m.get("role")!="system"]
        try: response=await gateway.generate(role="evaluator",messages=evaluator_messages,response_schema=schema)
        except GatewayError as exc: exc.stage=exc.stage or "evaluator"; raise
        try: return EvaluationResult.model_validate(response.structured_output)
        except (ValidationError,TypeError) as first:
            errors=first.errors(include_url=False) if isinstance(first,ValidationError) else [{"loc":[],"msg":"response was not one JSON object","type":"json_object"}]
            logger.warning({"role":"evaluator","model":response.model,"structured_output_mode":response.structured_output_mode,"validation_error_fields":[".".join(map(str,x.get("loc",[]))) for x in errors],"repair_attempted":True})
            raw=response.content
            repair_messages=[{"role":"system","content":self._repair_instruction(raw,errors,schema)}]
            try: repaired=await gateway.generate(role="evaluator",messages=repair_messages,response_schema=schema)
            except GatewayError as exc: exc.stage=exc.stage or "evaluator"; raise
            try:
                result=EvaluationResult.model_validate(repaired.structured_output); logger.info({"role":"evaluator","model":repaired.model,"repair_success":True}); return result
            except (ValidationError,TypeError) as second:
                logger.warning({"role":"evaluator","model":repaired.model,"repair_success":False})
                raise EvaluationError("STRUCTURED_OUTPUT_REPAIR_FAILED","The selected model returned output that did not match the evaluator schema after one repair attempt.") from second
