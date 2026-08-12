from __future__ import annotations

from ..models import PlanEnum


PLAN_FEATURES: dict[PlanEnum, set[str]] = {
    PlanEnum.FREE: {
        "basic_charts",
        "basic_statistics",
        "basic_cleaning",
        "saved_analyses",
        "history",
    },
    PlanEnum.STANDARD: {
        "basic_charts",
        "candlestick",
        "volume",
        "technical_indicators_basic",
        "statistics",
        "cleaning",
        "export_csv",
        "export_charts",
    },
    PlanEnum.PRO: {
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
    },
    PlanEnum.BUSINESS: {
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
    },
}


def can_use_feature(plan_id: str, feature: str) -> bool:
    try:
        plan = PlanEnum(plan_id)
    except ValueError:
        return False
    return feature in PLAN_FEATURES.get(plan, set())


def plan_allows_upload(plan_id: str, file_size_mb: float, row_count: int) -> bool:
    if plan_id == PlanEnum.FREE.value:
        return file_size_mb <= 5 and row_count <= 10000
    if plan_id == PlanEnum.STANDARD.value:
        return file_size_mb <= 25 and row_count <= 100000
    if plan_id == PlanEnum.PRO.value:
        return file_size_mb <= 250 and row_count <= 1000000
    if plan_id == PlanEnum.BUSINESS.value:
        return file_size_mb <= 1024 and row_count <= 5000000
    return False


def can_create_analysis(plan_id: str, current_saved: int, max_saved: int) -> bool:
    return current_saved < max_saved
