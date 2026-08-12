from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ..crud import get_all_plans, get_plan
from ..db import get_db
from ..schemas import PlanResponse

router = APIRouter(prefix="/plans", tags=["plans"])


@router.get("/", response_model=list[PlanResponse])
async def list_plans(db: AsyncSession = Depends(get_db)):
    return await get_all_plans(db)


@router.get("/{plan_id}", response_model=PlanResponse)
async def read_plan(plan_id: str, db: AsyncSession = Depends(get_db)):
    plan = await get_plan(db, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan no encontrado")
    return plan
