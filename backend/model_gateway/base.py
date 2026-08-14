from abc import ABC, abstractmethod
from typing import Any
from ..schemas.model import GatewayResponse

class GatewayError(RuntimeError):
    def __init__(self, error_type: str, message: str, *, stage: str | None = None):
        super().__init__(message); self.error_type = error_type; self.stage = stage

class ModelGateway(ABC):
    @abstractmethod
    async def generate(self, *, role: str, messages: list[dict[str, str]], response_schema: dict[str, Any] | None = None) -> GatewayResponse: ...
