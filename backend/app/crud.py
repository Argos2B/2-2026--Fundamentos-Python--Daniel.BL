from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Plan, PlanEnum, Subscription, SubscriptionStatus, User


async def get_user_by_google_id(session: AsyncSession, google_id: str) -> User | None:
    result = await session.execute(select(User).where(User.google_id == google_id))
    return result.scalars().first()


async def get_user_by_email(session: AsyncSession, email: str) -> User | None:
    result = await session.execute(select(User).where(User.email == email))
    return result.scalars().first()


async def create_user(session: AsyncSession, google_id: str, email: str, name: str | None = None, avatar_url: str | None = None) -> User:
    user = User(
        google_id=google_id,
        email=email,
        name=name,
        avatar_url=avatar_url,
        account_status="active",
        last_login=datetime.utcnow(),
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def update_last_login(session: AsyncSession, user: User) -> User:
    user.last_login = datetime.utcnow()
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def get_plan(session: AsyncSession, plan_id: str) -> Plan | None:
    result = await session.execute(select(Plan).where(Plan.id == plan_id))
    return result.scalars().first()


async def get_all_plans(session: AsyncSession) -> list[Plan]:
    result = await session.execute(select(Plan))
    return result.scalars().all()


async def get_active_subscription(session: AsyncSession, user_id: str) -> Subscription | None:
    result = await session.execute(
        select(Subscription)
        .where(Subscription.user_id == user_id)
        .where(Subscription.status == SubscriptionStatus.active)
        .order_by(Subscription.created_at.desc())
    )
    return result.scalars().first()


async def get_current_subscription(session: AsyncSession, user_id: str) -> Subscription | None:
    result = await session.execute(
        select(Subscription)
        .where(Subscription.user_id == user_id)
        .order_by(Subscription.created_at.desc())
    )
    return result.scalars().first()


async def create_subscription(session: AsyncSession, user_id: str, plan_id: str, status: SubscriptionStatus) -> Subscription:
    subscription = Subscription(
        user_id=user_id,
        plan_id=plan_id,
        status=status,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        current_period_start=datetime.utcnow() if status == SubscriptionStatus.active else None,
        current_period_end=(datetime.utcnow() + timedelta(days=30)) if status == SubscriptionStatus.active else None,
    )
    session.add(subscription)
    await session.commit()
    await session.refresh(subscription)
    return subscription


async def ensure_plans_exist(session: AsyncSession) -> list[Plan]:
    existing = await get_all_plans(session)
    if existing:
        return existing

    plans = [
        Plan(
            id=PlanEnum.FREE.value,
            name="Free",
            price="0.00",
            currency="USD",
            billing_interval="monthly",
            max_file_size_mb=5,
            max_rows=10000,
            monthly_file_limit=10,
            saved_analysis_limit=3,
            history_days=7,
            features=[
                "basic_charts",
                "basic_statistics",
                "basic_cleaning",
                "saved_analyses",
                "history",
            ],
            user_limit=1,
        ),
        Plan(
            id=PlanEnum.STANDARD.value,
            name="Standard",
            price="10.99",
            currency="USD",
            billing_interval="monthly",
            max_file_size_mb=25,
            max_rows=100000,
            monthly_file_limit=50,
            saved_analysis_limit=20,
            history_days=30,
            features=[
                "basic_charts",
                "candlestick",
                "volume",
                "technical_indicators_basic",
                "statistics",
                "cleaning",
                "export_csv",
                "export_charts",
            ],
            user_limit=1,
        ),
        Plan(
            id=PlanEnum.PRO.value,
            name="Pro",
            price="26.99",
            currency="USD",
            billing_interval="monthly",
            max_file_size_mb=250,
            max_rows=1000000,
            monthly_file_limit=250,
            saved_analysis_limit=100,
            history_days=365,
            features=[
                "basic_charts",
                "candlestick",
                "volume",
                "sma",
                "ema",
                "rsi",
                "macd",
                "bollinger",
                "advanced_statistics",
                "advanced_cleaning",
                "custom_dashboards",
                "ai_analysis",
                "export_csv",
                "export_png",
                "export_svg",
                "export_pdf",
            ],
            user_limit=1,
        ),
        Plan(
            id=PlanEnum.BUSINESS.value,
            name="Business",
            price="79.00",
            currency="USD",
            billing_interval="monthly",
            max_file_size_mb=1024,
            max_rows=5000000,
            monthly_file_limit=9999,
            saved_analysis_limit=9999,
            history_days=9999,
            features=[
                "basic_charts",
                "candlestick",
                "volume",
                "sma",
                "ema",
                "rsi",
                "macd",
                "bollinger",
                "advanced_statistics",
                "advanced_cleaning",
                "custom_dashboards",
                "ai_analysis",
                "export_csv",
                "export_png",
                "export_svg",
                "export_pdf",
                "api",
                "workspace",
                "priority_support",
                "unlimited_history",
            ],
            user_limit=5,
        ),
    ]

    session.add_all(plans)
    await session.commit()
    return plans
