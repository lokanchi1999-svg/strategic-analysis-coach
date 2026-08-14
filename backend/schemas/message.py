from datetime import datetime, timezone
from enum import StrEnum
from pydantic import BaseModel, Field

class MessageRole(StrEnum):
    STUDENT = "student"
    COACH = "coach"

class Message(BaseModel):
    role: MessageRole
    content: str = Field(min_length=1, max_length=50_000)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

