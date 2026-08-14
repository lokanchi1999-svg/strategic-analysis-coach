from pathlib import Path
import yaml
from ..schemas.case import CaseManifest, LoadedCase, PublicCase

class CaseNotFoundError(KeyError): pass
class InvalidCaseError(ValueError): pass

class FileCaseStore:
    def __init__(self, root: Path): self.root = root
    def _directory(self, code: str) -> Path:
        if not code or any(x in code for x in ("/", "\\", "..")): raise CaseNotFoundError(code)
        path = self.root / code
        # Windows paths are case-insensitive, while case codes are deliberately exact.
        exact_names = {entry.name for entry in self.root.iterdir() if entry.is_dir()}
        if code not in exact_names or not path.is_dir(): raise CaseNotFoundError(code)
        return path
    async def load(self, code: str) -> LoadedCase:
        directory = self._directory(code)
        try:
            manifest = CaseManifest.model_validate(yaml.safe_load((directory / "manifest.yaml").read_text("utf-8")))
            if manifest.case_code != code: raise InvalidCaseError("Directory and case_code do not match")
            material = (directory / "student_material.md").read_text("utf-8")
            hidden = yaml.safe_load((directory / "teacher_annotations.yaml").read_text("utf-8")) or {}
            return LoadedCase(manifest=manifest, student_material=material, teacher_annotations=hidden)
        except (OSError, yaml.YAMLError) as exc: raise InvalidCaseError(str(exc)) from exc
    async def public(self, code: str) -> PublicCase:
        case = await self.load(code)
        return PublicCase(manifest=case.manifest, student_material=case.student_material)
