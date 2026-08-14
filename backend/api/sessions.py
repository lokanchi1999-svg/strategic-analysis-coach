from fastapi import APIRouter, Response, status
from ..schemas.model import ModelCredentials
from ..schemas.session import CoachTurnResponse, PublicSessionView, SessionCreate, StudentMessageRequest
from .dependencies import cases, orchestrator, sessions, vault
from ..core.session_controller import SessionController
router = APIRouter(prefix="/api/sessions", tags=["sessions"]); controller = SessionController(sessions, cases)
@router.post("", response_model=PublicSessionView, status_code=201)
async def create_session(request: SessionCreate):
    state = await controller.create(request)
    if request.model_profile: await vault.set(state.session_id, request.model_profile, request.credentials or ModelCredentials())
    return PublicSessionView.from_internal(state)
@router.get("/{session_id}", response_model=PublicSessionView)
async def get_session(session_id: str): return PublicSessionView.from_internal(await sessions.get(session_id))
@router.post("/{session_id}/messages", response_model=CoachTurnResponse)
async def send_message(session_id: str, request: StudentMessageRequest): return await orchestrator.handle(session_id, request.content)
@router.delete("/{session_id}", status_code=204)
async def delete_session(session_id: str):
    await sessions.delete(session_id); await vault.delete(session_id); return Response(status_code=status.HTTP_204_NO_CONTENT)
