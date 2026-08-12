import re
from datetime import timedelta
from typing import Any, Optional

import pandas as pd

_COLUMN_ALIASES = {
    "timestamp": {"date", "fecha", "timestamp", "time", "datetime", "fecha_hora", "fechahora", "fecha-hora"},
    "open": {"open", "apertura", "opening", "inicio"},
    "high": {"high", "max", "maximo", "máximo", "alto"},
    "low": {"low", "min", "minimo", "mínimo", "bajo"},
    "close": {"close", "cierre", "closing", "fin"},
    "volume": {"volume", "volumen", "vol"},
}

_TIMEFRAMES = [
    (60, "1m"),
    (5 * 60, "5m"),
    (15 * 60, "15m"),
    (30 * 60, "30m"),
    (60 * 60, "1H"),
    (4 * 60 * 60, "4H"),
    (24 * 60 * 60, "1D"),
    (7 * 24 * 60 * 60, "1W"),
    (31 * 24 * 60 * 60, "1M"),
]


def _normalize_column_name(value: str) -> str:
    return re.sub(r"[\s_\-]+", "", str(value).strip().lower())


def _find_matches(columns: list[str], aliases: set[str]) -> Optional[str]:
    normalized = { _normalize_column_name(col): col for col in columns }
    for alias in aliases:
        normalized_alias = _normalize_column_name(alias)
        if normalized_alias in normalized:
            return normalized[normalized_alias]
    return None


def detect_ohlc(df: Optional[pd.DataFrame]) -> dict[str, Any]:
    result = {
        "is_ohlc": False,
        "timestamp_column": None,
        "open_column": None,
        "high_column": None,
        "low_column": None,
        "close_column": None,
        "volume_column": None,
        "available_timeframes": [],
    }
    if df is None or df.empty:
        return result

    columns = list(df.columns)
    result["timestamp_column"] = _find_matches(columns, _COLUMN_ALIASES["timestamp"])
    result["open_column"] = _find_matches(columns, _COLUMN_ALIASES["open"])
    result["high_column"] = _find_matches(columns, _COLUMN_ALIASES["high"])
    result["low_column"] = _find_matches(columns, _COLUMN_ALIASES["low"])
    result["close_column"] = _find_matches(columns, _COLUMN_ALIASES["close"])
    result["volume_column"] = _find_matches(columns, _COLUMN_ALIASES["volume"])

    if all(result.get(key) for key in ["timestamp_column", "open_column", "high_column", "low_column", "close_column"]):
        result["is_ohlc"] = True
        result["available_timeframes"] = get_timeframe_options(df, result["timestamp_column"])

    return result


def get_ohlc_frame(df: pd.DataFrame, metadata: dict[str, Any]) -> pd.DataFrame:
    timestamp_column = metadata.get("timestamp_column")
    ohlc_columns = [metadata.get("timestamp_column"), metadata.get("open_column"), metadata.get("high_column"), metadata.get("low_column"), metadata.get("close_column")]
    if not all(ohlc_columns):
        raise ValueError("Metadata incomplete para construir marco OHLC")

    ohlc_df = df.copy()
    ohlc_df = ohlc_df.loc[:, [timestamp_column, metadata["open_column"], metadata["high_column"], metadata["low_column"], metadata["close_column"]] + ([metadata["volume_column"]] if metadata.get("volume_column") else [])]
    ohlc_df[timestamp_column] = pd.to_datetime(ohlc_df[timestamp_column], errors="coerce")
    ohlc_df = ohlc_df.dropna(subset=[timestamp_column])
    ohlc_df = ohlc_df.sort_values(timestamp_column).reset_index(drop=True)
    return ohlc_df


def validate_ohlc(df: pd.DataFrame, metadata: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    if not metadata.get("is_ohlc"):
        errors.append("No se detectaron columnas OHLC suficientes.")
        return {"valid": False, "errors": errors}

    ohlc_df = get_ohlc_frame(df, metadata)
    if ohlc_df.empty:
        errors.append("Los datos OHLC no contienen filas válidas.")
        return {"valid": False, "errors": errors}

    timestamp_column = metadata["timestamp_column"]
    numeric_columns = [metadata["open_column"], metadata["high_column"], metadata["low_column"], metadata["close_column"]]
    for col in numeric_columns:
        if not pd.api.types.is_numeric_dtype(ohlc_df[col]):
            errors.append(f"La columna '{col}' debe contener valores numéricos.")

    if not (ohlc_df[metadata["high_column"]].ge(ohlc_df[metadata["low_column"]]).all()):
        errors.append("Los valores High deben ser mayores o iguales a Low en todas las filas.")

    open_col, close_col = metadata["open_column"], metadata["close_column"]
    price_range = ohlc_df[[open_col, close_col]].abs().max().max()
    if pd.api.types.is_numeric_dtype(ohlc_df[open_col]) and pd.api.types.is_numeric_dtype(ohlc_df[close_col]):
        if price_range == 0:
            errors.append("Open y Close contienen únicamente valores constantes o cero.")

    invalid_dates = ohlc_df[timestamp_column].isna().any()
    if invalid_dates:
        errors.append("Al menos una fecha no es válida.")

    return {"valid": len(errors) == 0, "errors": errors}


def get_timeframe_options(df: pd.DataFrame, timestamp_column: str) -> list[str]:
    if timestamp_column not in df.columns:
        return []

    timestamps = pd.to_datetime(df[timestamp_column], errors="coerce")
    if timestamps.isna().any():
        timestamps = timestamps.dropna()
    if timestamps.empty:
        return []

    timestamps = timestamps.sort_values().reset_index(drop=True)
    diffs = timestamps.diff().dt.total_seconds().dropna()
    if diffs.empty:
        return []

    min_delta = int(diffs.min())
    options: list[str] = []

    for seconds, label in _TIMEFRAMES:
        if min_delta <= seconds:
            options.append(label)

    # Always keep first valid resolution and larger groupings
    if "1D" not in options and any(diffs >= 24 * 60 * 60):
        options.append("1D")
    if "1W" not in options and any(diffs >= 7 * 24 * 60 * 60):
        options.append("1W")
    if "1M" not in options and any(diffs >= 28 * 24 * 60 * 60):
        options.append("1M")

    return [option for option in options if option != ""]


def _normalize_frequency_label(label: str) -> str:
    mapping = {
        "1m": "1min",
        "5m": "5min",
        "15m": "15min",
        "30m": "30min",
        "1H": "1H",
        "4H": "4H",
        "1D": "1D",
        "1W": "1W",
        "1M": "1M",
    }
    return mapping.get(label, label)


def resample_ohlc(df: pd.DataFrame, metadata: dict[str, Any], timeframe: str) -> pd.DataFrame:
    if not metadata.get("is_ohlc"):
        raise ValueError("No hay datos OHLC para el resampleo.")

    if timeframe not in get_timeframe_options(df, metadata["timestamp_column"]):
        return get_ohlc_frame(df, metadata)

    ohlc_df = get_ohlc_frame(df, metadata)
    timestamp = pd.to_datetime(ohlc_df[metadata["timestamp_column"]], errors="coerce")
    if timestamp.isna().any():
        raise ValueError("Los valores de fecha no son válidos para el resampleo.")

    ohlc_df = ohlc_df.set_index(timestamp)
    ohlc_df.index.name = metadata["timestamp_column"]
    rule = _normalize_frequency_label(timeframe)
    aggregation = {
        metadata["open_column"]: "first",
        metadata["high_column"]: "max",
        metadata["low_column"]: "min",
        metadata["close_column"]: "last",
    }
    if metadata.get("volume_column"):
        aggregation[metadata["volume_column"]] = "sum"

    resampled = ohlc_df.resample(rule).agg(aggregation)
    resampled = resampled.dropna(subset=[metadata["open_column"], metadata["high_column"], metadata["low_column"], metadata["close_column"]])
    resampled = resampled.reset_index()
    return resampled
