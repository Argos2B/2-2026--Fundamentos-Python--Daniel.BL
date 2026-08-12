from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, EmailStr, Field


class PlanIdentifier(str, Enum):
    FREE = "FREE"
    STANDARD = "STANDARD"
    PRO = "PRO"
    BUSINESS = "BUSINESS"


class UserBase(BaseModel):
    id: str
    google_id: str
    email: EmailStr
    name: str | None = None
    avatar_url: str | None = None
    account_status: str
    last_login: datetime | None = None

    model_config = {
        "from_attributes": True,
    }


class PlanBase(BaseModel):
    id: PlanIdentifier
    name: str
    price: float
    currency: str
    billing_interval: str
    max_file_size_mb: int
    max_rows: int
    monthly_file_limit: int
    saved_analysis_limit: int
    history_days: int
    features: list[str]
    user_limit: int

    model_config = {
        "from_attributes": True,
    }


class SubscriptionBase(BaseModel):
    id: str
    user_id: str
    plan_id: PlanIdentifier
    status: str
    provider: str | None = None
    provider_customer_id: str | None = None
    provider_subscription_id: str | None = None
    current_period_start: datetime | None = None
    current_period_end: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
    }


class UserResponse(UserBase):
    subscription: SubscriptionBase | None = None


class PlanResponse(PlanBase):
    pass


class SubscriptionResponse(SubscriptionBase):
    plan: PlanResponse


class OAuthUrlResponse(BaseModel):
    authorization_url: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = Field(default="bearer")


class AuthenticatedResponse(BaseModel):
    user: UserBase
    subscription: SubscriptionResponse | None = None
    token: str


class DashboardResponse(BaseModel):
    user: UserBase
    subscription: SubscriptionResponse | None = None

    model_config = {
        "from_attributes": True,
    }
