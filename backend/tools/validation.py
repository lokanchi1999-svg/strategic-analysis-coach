from __future__ import annotations
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable
import yaml
from pydantic import ValidationError
from ..schemas.case import CaseManifest
from ..schemas.skill import SkillManifest, SkillType

PLACEHOLDER_MARKERS=("TODO: Instructor content required", "TODO: Replace with instructor-provided", "DEVELOPMENT PLACEHOLDER", "NOT INSTRUCTOR-VALIDATED")

@dataclass
class ValidationReport:
    subject: str
    checks: list[str]=field(default_factory=list)
    warnings: list[str]=field(default_factory=list)
    errors: list[str]=field(default_factory=list)
    @property
    def valid(self): return not self.errors
    def render(self):
        lines=[f"Validating {self.subject}",""]
        # ASCII markers keep the CLI reliable on Windows consoles using GBK.
        lines += [f"[OK] {x}" for x in self.checks]+[f"[WARNING] {x}" for x in self.warnings]+[f"[ERROR] {x}" for x in self.errors]
        lines += ["", f"Validation {'passed' if self.valid else 'failed'} with {len(self.warnings)} warning(s) and {len(self.errors)} error(s)."]
        return "\n".join(lines)

def _yaml(path: Path): return yaml.safe_load(path.read_text("utf-8")) or {}
def _json(path: Path): return json.loads(path.read_text("utf-8"))
def _walk(value: Any) -> Iterable[tuple[str,Any]]:
    if isinstance(value,dict):
        for key,item in value.items():
            yield key,item; yield from _walk(item)
    elif isinstance(value,list):
        for item in value: yield from _walk(item)
def _ids(value): return [str(v) for k,v in _walk(value) if k=="id" and isinstance(v,(str,int))]
def _dimensions(value):
    values=[]
    for key,item in _walk(value):
        if key in {"dimension","dimension_id"} and isinstance(item,str): values.append(item)
        elif key=="dimensions" and isinstance(item,list): values.extend(x for x in item if isinstance(x,str))
    return values
def _levels(value):
    result=[]
    for key,item in _walk(value):
        if key.startswith("level_") and key[6:].isdigit(): result.append(int(key[6:]))
        if key in {"depth_level","level"} and isinstance(item,int): result.append(item)
    return result
def _warn_placeholders(report,path,data):
    text=json.dumps(data,ensure_ascii=False) if not isinstance(data,str) else data
    if any(marker in text for marker in PLACEHOLDER_MARKERS): report.warnings.append(f"{path.name} contains instructor-content placeholder")

def validate_skill(path: Path) -> ValidationReport:
    report=ValidationReport(f"skill: {path.name}")
    if not (path/"manifest.yaml").is_file(): report.errors.append("missing required files: manifest.yaml"); return report
    try: manifest=SkillManifest.model_validate(_yaml(path/"manifest.yaml")); report.checks.append("manifest.yaml valid")
    except (OSError,yaml.YAMLError,ValidationError) as exc: report.errors.append(f"manifest invalid: {exc}"); return report
    required=("manifest.yaml","ontology.yaml","rubric.yaml","questioning_policy.yaml") if manifest.type==SkillType.ANALYSIS else ("manifest.yaml",)
    missing=[name for name in required if not (path/name).is_file()]
    if missing: report.errors.append("missing required files: "+", ".join(missing)); return report
    report.checks.append("required files present")
    if manifest.id!=path.name: report.errors.append(f"directory name must match manifest id: {manifest.id}")
    parsed={}
    for name in required[1:]:
        try: parsed[name]=_yaml(path/name); report.checks.append(f"{name} valid")
        except (OSError,yaml.YAMLError) as exc: report.errors.append(f"{name} invalid: {exc}")
    known=set(manifest.dimensions)
    for name,data in parsed.items():
        for dimension in set(_dimensions(data))-known: report.errors.append(f"{name} references unknown dimension: {dimension}")
        for level in set(_levels(data))-set(manifest.depth_levels): report.errors.append(f"{name} references undeclared depth level: {level}")
        _warn_placeholders(report,path/name,data)
    all_ids=[]
    for data in parsed.values(): all_ids.extend(_ids(data))
    for optional in ("misconceptions.yaml","examples.json"):
        target=path/optional
        if target.exists():
            try:
                data=_json(target) if target.suffix==".json" else _yaml(target); all_ids.extend(_ids(data)); _warn_placeholders(report,target,data)
            except (OSError,yaml.YAMLError,json.JSONDecodeError) as exc: report.errors.append(f"{optional} invalid: {exc}")
    duplicates=sorted({item for item in all_ids if all_ids.count(item)>1})
    if duplicates: report.errors.append("duplicate item ids: "+", ".join(duplicates))
    report.checks.append(f"{len(manifest.dimensions)} dimensions registered")
    report.checks.append("depth levels consistent")
    return report

def validate_case(path: Path, project_root: Path) -> ValidationReport:
    report=ValidationReport(f"case: {path.name}"); required=("manifest.yaml","student_material.md","teacher_annotations.yaml")
    missing=[name for name in required if not (path/name).is_file()]
    if missing: report.errors.append("missing required files: "+", ".join(missing)); return report
    report.checks.append("required files present")
    try: manifest=CaseManifest.model_validate(_yaml(path/"manifest.yaml")); report.checks.append("manifest valid")
    except (OSError,yaml.YAMLError,ValidationError) as exc: report.errors.append(f"manifest invalid: {exc}"); return report
    if manifest.case_code!=path.name: report.errors.append(f"directory name must exactly match case_code: {manifest.case_code}")
    else: report.checks.append("case code matches directory")
    skill_paths=list((project_root/"skills").glob(f"*/{manifest.skill_id}/manifest.yaml"))
    if skill_paths: report.checks.append(f"referenced skill exists: {manifest.skill_id}")
    else: report.errors.append(f"referenced skill does not exist: {manifest.skill_id}")
    instructor=project_root/"instructors"/manifest.instructor_id/"profile.yaml"
    if instructor.is_file(): report.checks.append(f"instructor exists: {manifest.instructor_id}")
    else: report.errors.append(f"instructor does not exist: {manifest.instructor_id}")
    if (path/"student_material.md").read_text("utf-8").strip(): report.checks.append("student_material.md non-empty")
    else: report.errors.append("student_material.md must not be empty")
    try:
        hidden=_yaml(path/"teacher_annotations.yaml"); report.checks.append("teacher_annotations.yaml valid"); _warn_placeholders(report,path/"teacher_annotations.yaml",hidden)
    except (OSError,yaml.YAMLError) as exc: report.errors.append(f"teacher_annotations.yaml invalid: {exc}")
    return report
