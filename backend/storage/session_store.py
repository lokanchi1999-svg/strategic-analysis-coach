from abc import ABC, abstractmethod
import asyncio
from ..schemas.session import SessionState

class SessionNotFoundError(KeyError): pass

class SessionStore(ABC):
    @abstractmethod
    async def get(self, session_id: str) -> SessionState: ...
    @abstractmethod
    async def save(self, state: SessionState) -> None: ...
    @abstractmethod
    async def delete(self, session_id: str) -> None: ...

class InMemorySessionStore(SessionStore):
    def __init__(self):
        self._items: dict[str, SessionState] = {}
        self._lock = asyncio.Lock()
    async def get(self, session_id: str) -> SessionState:
        async with self._lock:
            if session_id not in self._items: raise SessionNotFoundError(session_id)
            return self._items[session_id].model_copy(deep=True)
    async def save(self, state: SessionState) -> None:
        async with self._lock: self._items[state.session_id] = state.model_copy(deep=True)
    async def delete(self, session_id: str) -> None:
        async with self._lock:
            if self._items.pop(session_id, None) is None: raise SessionNotFoundError(session_id)

