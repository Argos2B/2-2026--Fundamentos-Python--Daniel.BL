from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import get_current_user
from ..crud import get_current_subscription
from ..db import get_db
from ..schemas import DashboardResponse, SubscriptionResponse

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/me", response_model=DashboardResponse)
async def read_dashboard(user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    subscription = await get_current_subscription(db, str(user.id))
    return DashboardResponse(
        user=user,
        subscription=SubscriptionResponse.from_orm(subscription) if subscription else None,
    )
