from pathlib import Path
import json, yaml
from pydantic import ValidationError
from ..schemas.skill import SkillManifest

class SkillNotFoundError(KeyError): pass
class InvalidSkillError(ValueError): pass

class FileSkillStore:
    REQUIRED_ANALYSIS = ("manifest.yaml", "ontology.yaml", "rubric.yaml", "questioning_policy.yaml")
    def __init__(self, root: Path): self.root = root
    def _paths(self): return list((self.root / "analysis").glob("*/manifest.yaml")) + list((self.root / "meta").glob("*/manifest.yaml"))
    async def list(self) -> list[SkillManifest]:
        return [self._manifest(path.parent) for path in self._paths()]
    def _directory(self, skill_id: str) -> Path:
        for group in ("analysis", "meta"):
            path = self.root / group / skill_id
            if path.is_dir(): return path
        raise SkillNotFoundError(skill_id)
    def _manifest(self, directory: Path) -> SkillManifest:
        try: return SkillManifest.model_validate(yaml.safe_load((directory / "manifest.yaml").read_text("utf-8")))
        except (OSError, yaml.YAMLError, ValidationError) as exc: raise InvalidSkillError(f"Invalid skill manifest at {directory}: {exc}") from exc
    async def load(self, skill_id: str) -> dict:
        directory = self._directory(skill_id); manifest = self._manifest(directory)
        if manifest.id != skill_id: raise InvalidSkillError("Directory and skill id do not match")
        required = self.REQUIRED_ANALYSIS if manifest.type == "analysis" else ("manifest.yaml",)
        missing = [name for name in required if not (directory / name).exists()]
        if missing: raise InvalidSkillError(f"Missing required files: {', '.join(missing)}")
        result = {"manifest": manifest.model_dump()}
        for path in directory.iterdir():
            if path.suffix in (".yaml", ".yml") and path.name != "manifest.yaml": result[path.stem] = yaml.safe_load(path.read_text("utf-8"))
            elif path.suffix == ".json": result[path.stem] = json.loads(path.read_text("utf-8"))
        return result

