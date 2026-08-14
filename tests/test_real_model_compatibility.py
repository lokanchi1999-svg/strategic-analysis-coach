import json
import httpx
import pytest
from backend.core.evaluator import EvaluationError,Evaluator
from backend.model_gateway.base import GatewayError,ModelGateway
from backend.model_gateway.openai_compatible import OpenAICompatibleGateway
from backend.schemas.model import GatewayResponse,ModelCredentials,ModelProfile,StructuredOutputMode

VALID={"skill_id":"five_forces","dimension":"supplier_power","depth_level":1,"claim_quality":"partial","evidence_quality":"missing","mechanism_quality":"missing","integration_quality":"missing","case_fact_accuracy":"unknown","missing_fact_ids":[],"misconceptions":[],"advance":False,"recommended_action":"PROBE_EVIDENCE","confidence":0.8,"notes":None}

class SequenceGateway(ModelGateway):
    def __init__(self,items): self.items=list(items); self.calls=[]
    async def generate(self,**kwargs):
        self.calls.append(kwargs)
        item=self.items.pop(0)
        if isinstance(item,Exception): raise item
        return GatewayResponse(content=json.dumps(item),structured_output=item,model="fake")

@pytest.mark.asyncio
async def test_wrong_coach_message_is_repaired_once():
    gateway=SequenceGateway([{"role":"coach","content":"Let's begin."},VALID])
    result=await Evaluator().evaluate(gateway,[{"role":"user","content":"claim"}])
    assert result.skill_id=="five_forces" and len(gateway.calls)==2
    assert "JSON Schema" in gateway.calls[0]["messages"][0]["content"]
    assert "Do not add role/content/type" in gateway.calls[1]["messages"][0]["content"]

@pytest.mark.asyncio
async def test_repair_failure_is_controlled_and_bounded():
    gateway=SequenceGateway([{"type":"coach_message","content":"x"},{"role":"coach","content":"x"}])
    with pytest.raises(EvaluationError) as caught: await Evaluator().evaluate(gateway,[])
    assert caught.value.error_type=="STRUCTURED_OUTPUT_REPAIR_FAILED" and len(gateway.calls)==2

@pytest.mark.asyncio
async def test_valid_first_attempt_does_not_repair():
    gateway=SequenceGateway([VALID]); await Evaluator().evaluate(gateway,[]); assert len(gateway.calls)==1

def profile(mode="auto",timeout=1):
    return ModelProfile(adapter="openai_compatible",base_url="https://provider.test/v1",structured_output_mode=mode,models={"default":"test"},generation={"timeout_seconds":timeout,"temperature":0.2,"max_output_tokens":100})

@pytest.mark.asyncio
async def test_auto_falls_back_schema_then_json_object_only_on_unsupported():
    modes=[]
    def handler(request):
        body=json.loads(request.content); modes.append(body.get("response_format",{}).get("type"))
        if len(modes)==1:return httpx.Response(400,json={"error":"unsupported"})
        return httpx.Response(200,json={"choices":[{"message":{"content":json.dumps(VALID)}}],"model":"test"})
    gateway=OpenAICompatibleGateway(profile(),ModelCredentials(api_key="secret"),httpx.MockTransport(handler))
    response=await gateway.generate(role="evaluator",messages=[],response_schema={"type":"object"})
    assert modes==["json_schema","json_object"] and response.structured_output==VALID

@pytest.mark.asyncio
async def test_timeout_retries_once_and_never_capability_fallbacks():
    calls=0
    def handler(request):
        nonlocal calls; calls+=1; raise httpx.ReadTimeout("slow",request=request)
    gateway=OpenAICompatibleGateway(profile(),ModelCredentials(api_key="secret"),httpx.MockTransport(handler))
    with pytest.raises(GatewayError) as caught: await gateway.generate(role="evaluator",messages=[],response_schema={"type":"object"})
    assert caught.value.error_type=="MODEL_TIMEOUT" and calls==2

@pytest.mark.asyncio
async def test_authentication_is_not_retried_or_fallbacked():
    calls=0
    def handler(request):
        nonlocal calls; calls+=1; return httpx.Response(401,json={})
    gateway=OpenAICompatibleGateway(profile(),ModelCredentials(api_key="bad"),httpx.MockTransport(handler))
    with pytest.raises(GatewayError) as caught: await gateway.generate(role="evaluator",messages=[],response_schema={"type":"object"})
    assert caught.value.error_type=="MODEL_AUTHENTICATION_FAILED" and calls==1

def test_prompt_only_conservative_parser_rejects_prose():
    assert OpenAICompatibleGateway._parse_object('Here is JSON: {"x":1}') is None
    assert OpenAICompatibleGateway._parse_object('```json\n{"x":1}\n```') is None
    assert OpenAICompatibleGateway._parse_object('{"x":1}')=={"x":1}
