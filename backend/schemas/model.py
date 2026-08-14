from enum import StrEnum
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, SecretStr

class StructuredOutputMode(StrEnum):
    AUTO = "auto"
    JSON_SCHEMA = "json_schema"
    JSON_OBJECT = "json_object"
    PROMPT_ONLY = "prompt_only"

class RoleModels(BaseModel):
    model_config = ConfigDict(extra="forbid")
    default: str
    evaluator: str | None = None
    question_generator: str | None = None
    framework_selector: str | None = None
    def resolve(self, role: str) -> str:
        return getattr(self, role, None) or self.default

class GenerationSettings(BaseModel):
    model_config = ConfigDict(extra="forbid")
    temperature: float = Field(default=0.2, ge=0, le=2)
    max_output_tokens: int = Field(default=1500, ge=1, le=100_000)
    timeout_seconds: float = Field(default=60, gt=0, le=300)

class ModelProfile(BaseModel):
    model_config = ConfigDict(extra="forbid")
    profile_name: str = "Session API"
    adapter: Literal["mock", "openai_compatible"] = "mock"
    base_url: str = "https://api.openai.com/v1"
    structured_output_mode: StructuredOutputMode = StructuredOutputMode.AUTO
    models: RoleModels = Field(default_factory=lambda: RoleModels(default="mock-model"))
    generation: GenerationSettings = Field(default_factory=GenerationSettings)

class ModelCredentials(BaseModel):
    model_config = ConfigDict(extra="forbid")
    api_key: SecretStr | None = None

class ModelTestRequest(BaseModel):
    profile: ModelProfile
    credentials: ModelCredentials = Field(default_factory=ModelCredentials)

class ModelTestResponse(BaseModel):
    success: bool
    message: str
    model: str | None = None
    error_type: str | None = None
    checks: dict[str, bool] = Field(default_factory=dict)
    structured_output_mode: StructuredOutputMode | None = None

class GatewayUsage(BaseModel):
    input_tokens: int | None = None
    output_tokens: int | None = None

class GatewayResponse(BaseModel):
    content: str
    structured_output: dict | None = None
    usage: GatewayUsage = Field(default_factory=GatewayUsage)
    model: str
    latency_ms: float | None = None
    structured_output_mode: StructuredOutputMode | None = None
