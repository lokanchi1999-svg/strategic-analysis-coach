"""Frozen v0.2 Skill package contracts."""
from enum import StrEnum
from pydantic import BaseModel, ConfigDict, Field, field_validator

class SkillType(StrEnum): ANALYSIS="analysis"; META="meta"
class LocalizedName(BaseModel):
    model_config=ConfigDict(extra="forbid")
    en: str=Field(min_length=1); zh: str=Field(min_length=1)
class SkillManifest(BaseModel):
    model_config=ConfigDict(extra="forbid")
    id: str=Field(pattern=r"^[a-z][a-z0-9_]*$")
    type: SkillType
    version: str=Field(pattern=r"^\d+\.\d+\.\d+$")
    name: LocalizedName
    dimensions: list[str]=Field(default_factory=list)
    depth_levels: list[int]=Field(default_factory=list)
    @field_validator("dimensions")
    @classmethod
    def dimensions_unique(cls,value):
        if len(value)!=len(set(value)): raise ValueError("dimensions must be unique")
        return value
    @field_validator("depth_levels")
    @classmethod
    def levels_unique_positive(cls,value):
        if len(value)!=len(set(value)) or any(x<1 for x in value): raise ValueError("depth_levels must contain unique positive integers")
        return value
