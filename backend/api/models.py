from fastapi import APIRouter
from ..core.evaluator import EvaluationError, Evaluator
from ..model_gateway.base import GatewayError
from ..model_gateway.registry import create_gateway
from ..schemas.model import ModelTestRequest, ModelTestResponse

router=APIRouter(prefix="/api/model",tags=["model"])
@router.post("/test",response_model=ModelTestResponse)
async def test_model(request:ModelTestRequest):
    checks={"provider_reachable":False,"authentication":False,"basic_completion":False,"structured_output":False,"evaluation_schema":False}
    gateway=create_gateway(request.profile,request.credentials); model=None
    try:
        basic=await gateway.generate(role="default",messages=[{"role":"user","content":"Reply with OK."}]); model=basic.model
        checks.update(provider_reachable=True,authentication=True,basic_completion=True)
        synthetic=[{"role":"user","content":"DEVELOPMENT-ONLY protocol test. Classify a placeholder response; no case or teacher data is provided."}]
        await Evaluator().evaluate(gateway,synthetic)
        checks.update(structured_output=True,evaluation_schema=True)
        mode=getattr(gateway,"last_structured_output_mode",request.profile.structured_output_mode)
        return ModelTestResponse(success=True,checks=checks,structured_output_mode=mode,message="Model is compatible with Strategic Analysis Coach.",model=model)
    except EvaluationError:
        return ModelTestResponse(success=False,checks=checks,structured_output_mode=getattr(gateway,"last_structured_output_mode",None),message="The model is reachable, but evaluator structured output validation failed.",model=model,error_type="EVALUATOR_COMPATIBILITY_FAILED")
    except GatewayError as exc:
        error_type="EVALUATOR_COMPATIBILITY_FAILED" if checks["basic_completion"] and exc.error_type not in {"MODEL_TIMEOUT","MODEL_AUTHENTICATION_FAILED","MODEL_RATE_LIMITED"} else exc.error_type
        return ModelTestResponse(success=False,checks=checks,structured_output_mode=getattr(gateway,"last_structured_output_mode",None),message=str(exc),model=model,error_type=error_type)
