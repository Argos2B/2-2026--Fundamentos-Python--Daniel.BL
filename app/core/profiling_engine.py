"""Dataset profiling and quality warnings."""
from __future__ import annotations

from typing import Any

import pandas as pd


class ProfilingEngine:
    """Generates a quick dataset profile and quality alerts."""

    def __init__(self, data_manager: Any):
        self.dm = data_manager

    def profile(self) -> dict[str, Any]:
        if not self.dm.has_data():
            return {"rows": 0, "columns": 0, "warnings": []}

        df = self.dm.df
        warnings: list[str] = []

        null_ratio = (df.isna().sum().sum() / (df.shape[0] * df.shape[1])) if df.shape[0] and df.shape[1] else 0
        if null_ratio > 0:
            warnings.append(f"Se detectaron datos faltantes en {int(df.isna().sum().sum())} celdas.")

        duplicate_count = int(df.duplicated().sum())
        if duplicate_count:
            warnings.append(f"Se detectaron {duplicate_count} filas duplicadas.")

        text_cols = df.select_dtypes(include=[object]).columns
        for col in text_cols:
            invalid = df[col].astype(str).str.contains(r"^\s*$|^\s*None\s*$", case=False, na=False).sum()
            if invalid:
                warnings.append(f"La columna '{col}' tiene {int(invalid)} valores vacíos o inconsistentes.")

        numeric_cols = df.select_dtypes(include=['number']).columns
        for col in numeric_cols:
            series = df[col].dropna()
            if series.empty:
                continue
            q1 = series.quantile(0.25)
            q3 = series.quantile(0.75)
            iqr = q3 - q1
            lower = q1 - 1.5 * iqr
            upper = q3 + 1.5 * iqr
            outliers = series[(series < lower) | (series > upper)].count()
            if outliers:
                warnings.append(f"La columna '{col}' contiene {int(outliers)} valores fuera del rango esperado.")

        return {
            "rows": len(df),
            "columns": len(df.columns),
            "null_ratio": round(float(null_ratio * 100), 2),
            "duplicates": duplicate_count,
            "numeric_columns": int(len(df.select_dtypes(include=['number']).columns)),
            "text_columns": int(len(df.select_dtypes(include=[object]).columns)),
            "date_columns": int(len(df.select_dtypes(include=['datetime64[ns]']).columns)),
            "warnings": warnings,
        }
