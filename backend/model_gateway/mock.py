from ..schemas.model import GatewayResponse
from .base import ModelGateway

class MockModelGateway(ModelGateway):
    async def generate(self, *, role: str, messages: list[dict[str, str]], response_schema=None) -> GatewayResponse:
        if role == "evaluator":
            data = {"skill_id":"five_forces","dimension":"supplier_power","depth_level":1,"claim_quality":"partial","evidence_quality":"missing","mechanism_quality":"missing","integration_quality":"missing","case_fact_accuracy":"unknown","missing_fact_ids":[],"misconceptions":[],"advance":False,"recommended_action":"PROBE_EVIDENCE","confidence":0.8}
            return GatewayResponse(content="", structured_output=data, model="mock-model")
        return GatewayResponse(content="你能指出材料中哪些具体事实支持这个判断吗？", model="mock-model")

