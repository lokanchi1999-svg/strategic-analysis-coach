from ..schemas.model import ModelCredentials, ModelProfile
from .base import ModelGateway
from .mock import MockModelGateway
from .openai_compatible import OpenAICompatibleGateway

def create_gateway(profile: ModelProfile, credentials: ModelCredentials | None = None) -> ModelGateway:
    if profile.adapter == "mock": return MockModelGateway()
    if profile.adapter == "openai_compatible": return OpenAICompatibleGateway(profile, credentials or ModelCredentials())
    raise ValueError(f"Unknown adapter: {profile.adapter}")

