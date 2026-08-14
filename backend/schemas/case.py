"""Separate public and internal Case contracts."""
from typing import Any
from pydantic import BaseModel, ConfigDict, Field
class CaseManifest(BaseModel):
    model_config=ConfigDict(extra="forbid")
    case_code: str=Field(pattern=r"^[A-Z0-9]+(?:-[A-Z0-9]+)*$")
    title: str=Field(min_length=1)
    skill_id: str=Field(pattern=r"^[a-z][a-z0-9_]*$")
    instructor_id: str=Field(min_length=1,pattern=r"^[a-zA-Z0-9_-]+$")
    language: str=Field(pattern=r"^[a-z]{2}(?:-[A-Z]{2})?$")
class PublicCase(BaseModel):
    model_config=ConfigDict(extra="forbid")
    manifest: CaseManifest; student_material: str
class InternalCase(BaseModel):
    model_config=ConfigDict(extra="forbid")
    manifest: CaseManifest; student_material: str; teacher_annotations: dict[str,Any]
LoadedCase=InternalCase
