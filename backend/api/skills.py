from fastapi import APIRouter
from .dependencies import skills
router = APIRouter(prefix="/api/skills", tags=["skills"])
@router.get("")
async def list_skills(): return await skills.list()

