from pathlib import Path
from ..core.context_builder import ContextBuilder
from ..core.orchestrator import Orchestrator
from ..model_gateway.credentials import SessionCredentialVault
from ..storage.case_store import FileCaseStore
from ..storage.session_store import InMemorySessionStore
from ..storage.skill_store import FileSkillStore

ROOT = Path(__file__).resolve().parents[2]
sessions = InMemorySessionStore(); cases = FileCaseStore(ROOT / "cases"); skills = FileSkillStore(ROOT / "skills"); vault = SessionCredentialVault()
orchestrator = Orchestrator(sessions, cases, skills, vault, ContextBuilder(ROOT / "coach_core" / "core_policy.md"))

