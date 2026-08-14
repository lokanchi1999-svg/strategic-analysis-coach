import json
from backend.model_gateway.base import GatewayError,ModelGateway
from backend.schemas.model import GatewayResponse
from backend.core.evaluator import EvaluationError
from backend.api import models as model_api
from backend.api.dependencies import orchestrator

VALID={"skill_id":"five_forces","dimension":None,"depth_level":1,"claim_quality":"partial","evidence_quality":"missing","mechanism_quality":"missing","integration_quality":"missing","case_fact_accuracy":"unknown","missing_fact_ids":[],"misconceptions":[],"advance":False,"recommended_action":"PROBE_EVIDENCE","confidence":0.8,"notes":None}
class CompatibilityGateway(ModelGateway):
    def __init__(self,evaluator): self.evaluator=evaluator
    async def generate(self,*,role,**kwargs):
        if role=="default": return GatewayResponse(content="OK",model="fake")
        if isinstance(self.evaluator,Exception): raise self.evaluator
        return GatewayResponse(content=json.dumps(self.evaluator),structured_output=self.evaluator,model="fake")

def payload(): return {"profile":{"adapter":"mock","models":{"default":"fake"}},"credentials":{}}
def test_compatibility_success(client,monkeypatch):
    monkeypatch.setattr(model_api,"create_gateway",lambda *x:CompatibilityGateway(VALID))
    body=client.post("/api/model/test",json=payload()).json()
    assert body["success"] and all(body["checks"].values())
def test_compatibility_invalid_evaluator(client,monkeypatch):
    monkeypatch.setattr(model_api,"create_gateway",lambda *x:CompatibilityGateway({"role":"coach","content":"x"}))
    body=client.post("/api/model/test",json=payload()).json()
    assert not body["success"] and body["error_type"]=="EVALUATOR_COMPATIBILITY_FAILED"
def test_compatibility_timeout(client,monkeypatch):
    monkeypatch.setattr(model_api,"create_gateway",lambda *x:CompatibilityGateway(GatewayError("MODEL_TIMEOUT","slow")))
    body=client.post("/api/model/test",json=payload()).json(); assert not body["success"] and body["error_type"]=="MODEL_TIMEOUT"
def test_compatibility_auth_error_has_no_fallback(client,monkeypatch):
    class Auth(ModelGateway):
        calls=0
        async def generate(self,**kwargs): self.calls+=1; raise GatewayError("MODEL_AUTHENTICATION_FAILED","bad key")
    gateway=Auth(); monkeypatch.setattr(model_api,"create_gateway",lambda *x:gateway)
    body=client.post("/api/model/test",json=payload()).json(); assert body["error_type"]=="MODEL_AUTHENTICATION_FAILED" and gateway.calls==1

def test_controlled_model_error_keeps_cors_header(client,monkeypatch):
    class FailEvaluator:
        async def evaluate(self,*args): raise EvaluationError("INVALID_STRUCTURED_OUTPUT","invalid")
    monkeypatch.setattr(orchestrator,"evaluator",FailEvaluator())
    created=client.post("/api/sessions",json={"mode":"guided","case_code":"SAMPLE-CASE-01"}).json()
    response=client.post(f"/api/sessions/{created['session_id']}/messages",headers={"Origin":"http://localhost:3000"},json={"content":"claim"})
    assert response.status_code==502 and response.headers["access-control-allow-origin"]=="http://localhost:3000"
    assert response.json()["stage"]=="evaluator" and response.json()["error_type"]=="INVALID_STRUCTURED_OUTPUT"
    stored=client.get(f"/api/sessions/{created['session_id']}").json()
    assert stored["current_depth"]==0 and stored["last_evaluation"] is None
