from fastapi import APIRouter
from ..schemas.case import PublicCase
from .dependencies import cases
router = APIRouter(prefix="/api/cases", tags=["cases"])
@router.get("/{case_code}", response_model=PublicCase)
async def get_case(case_code: str): return await cases.public(case_code)

