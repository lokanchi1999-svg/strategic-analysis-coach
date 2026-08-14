import asyncio
from ..schemas.model import ModelCredentials, ModelProfile

class SessionCredentialVault:
    """Process-memory-only BYOK vault. Values are never serialized with SessionState."""
    def __init__(self): self._items = {}; self._lock = asyncio.Lock()
    async def set(self, session_id: str, profile: ModelProfile, credentials: ModelCredentials):
        async with self._lock: self._items[session_id] = (profile, credentials)
    async def get(self, session_id: str):
        async with self._lock: return self._items.get(session_id)
    async def delete(self, session_id: str):
        async with self._lock: self._items.pop(session_id, None)

