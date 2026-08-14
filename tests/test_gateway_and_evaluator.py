import pytest
from backend.core.evaluator import EvaluationError, Evaluator
from backend.model_gateway.base import ModelGateway
from backend.model_gateway.mock import MockModelGateway
from backend.schemas.model import GatewayResponse

@pytest.mark.asyncio
async def test_mock_gateway_evaluation():
    result = await Evaluator().evaluate(MockModelGateway(), [])
    assert result.recommended_action == "PROBE_EVIDENCE"

class BrokenGateway(ModelGateway):
    async def generate(self, **kwargs):
        return GatewayResponse(content="not-json", structured_output={"wrong":True}, model="broken")

@pytest.mark.asyncio
async def test_invalid_evaluation_is_caught():
    with pytest.raises(EvaluationError):
        await Evaluator().evaluate(BrokenGateway(), [])
