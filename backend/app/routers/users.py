from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import get_current_user
from ..crud import get_current_subscription
from ..db import get_db
from ..schemas import UserResponse, SubscriptionResponse

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
async def read_current_user(user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    subscription = await get_current_subscription(db, str(user.id))
    return UserResponse(
        id=str(user.id),
        google_id=user.google_id,
        email=user.email,
        name=user.name,
        avatar_url=user.avatar_url,
        account_status=user.account_status,
        last_login=user.last_login,
        subscription=SubscriptionResponse.from_orm(subscription) if subscription else None,
    )
