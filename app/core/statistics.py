"""Statistical analysis engine."""
import pandas as pd
import numpy as np
from scipy import stats as scipy_stats
from app.core.data_manager import DataManager


class StatisticsEngine:
    """Provides descriptive, inferential and diagnostic statistics."""

    def __init__(self, data_manager: DataManager):
        self.dm = data_manager

    # ── Descriptive ────────────────────────────────────────────────────

    def descriptive_stats(self) -> pd.DataFrame:
        if not self.dm.has_data():
            return pd.DataFrame()

        numeric = self.dm.df.select_dtypes(include=[np.number])
        if numeric.empty:
            return pd.DataFrame()

        desc = numeric.describe().T
        desc["missing"] = numeric.isna().sum()
        desc["missing_%"] = (numeric.isna().sum() / len(numeric) * 100).round(2)
        desc["median"] = numeric.median()
        desc["skew"] = numeric.skew().round(4)
        desc["kurtosis"] = numeric.kurtosis().round(4)
        desc["range"] = desc["max"] - desc["min"]

        col_order = [
            "count", "missing", "missing_%", "mean", "median", "std",
            "min", "25%", "50%", "75%", "max", "range", "skew", "kurtosis",
        ]
        available = [c for c in col_order if c in desc.columns]
        return desc[available].round(4)

    # ── Single column ──────────────────────────────────────────────────

    def column_stats(self, column: str) -> dict:
        if not self.dm.has_data() or column not in self.dm.df.columns:
            return {}

        series = self.dm.df[column]
        stats: dict = {
            "nombre": column,
            "tipo": str(series.dtype),
            "total": len(series),
            "no_nulos": int(series.count()),
            "nulos": int(series.isna().sum()),
            "nulos_%": round(series.isna().sum() / len(series) * 100, 2),
            "únicos": int(series.nunique()),
        }

        if pd.api.types.is_numeric_dtype(series) and not series.isna().all():
            stats.update({
                "media": round(float(series.mean()), 4),
                "mediana": round(float(series.median()), 4),
                "std": round(float(series.std()), 4),
                "min": round(float(series.min()), 4),
                "max": round(float(series.max()), 4),
                "q1": round(float(series.quantile(0.25)), 4),
                "q3": round(float(series.quantile(0.75)), 4),
                "rango": round(float(series.max() - series.min()), 4),
                "varianza": round(float(series.var()), 4),
                "asimetría": round(float(series.skew()), 4),
                "curtosis": round(float(series.kurtosis()), 4),
            })
        else:
            mode_val = series.mode()
            vc = series.value_counts()
            stats.update({
                "moda": str(mode_val.iloc[0]) if not mode_val.empty else "N/A",
                "freq_moda": int(vc.iloc[0]) if not vc.empty else 0,
            })

        return stats

    # ── Correlation ────────────────────────────────────────────────────

    def correlation_matrix(self) -> pd.DataFrame:
        if not self.dm.has_data():
            return pd.DataFrame()
        numeric = self.dm.df.select_dtypes(include=[np.number])
        if numeric.empty:
            return pd.DataFrame()
        return numeric.corr().round(4)

    # ── Missing analysis ───────────────────────────────────────────────

    def missing_analysis(self) -> pd.DataFrame:
        if not self.dm.has_data():
            return pd.DataFrame()

        missing = self.dm.df.isna().sum()
        total = len(self.dm.df)

        result = pd.DataFrame({
            "Columna": self.dm.df.columns,
            "Tipo": [str(dt) for dt in self.dm.df.dtypes],
            "No Nulos": [int(self.dm.df[col].count()) for col in self.dm.df.columns],
            "Faltantes": [int(missing[col]) for col in self.dm.df.columns],
            "% Faltantes": [
                round(missing[col] / total * 100, 2) for col in self.dm.df.columns
            ],
            "% Completo": [
                round((1 - missing[col] / total) * 100, 2)
                for col in self.dm.df.columns
            ],
        })
        return result.sort_values("Faltantes", ascending=False).reset_index(drop=True)

    # ── Normality test ─────────────────────────────────────────────────

    def distribution_test(self, column: str) -> dict:
        if not self.dm.has_data() or column not in self.dm.df.columns:
            return {}

        series = self.dm.df[column].dropna()
        if not pd.api.types.is_numeric_dtype(series) or len(series) < 8:
            return {"error": "Se necesitan al menos 8 valores numéricos"}

        sample = (
            series.sample(min(5000, len(series)), random_state=42)
            if len(series) > 5000
            else series
        )
        try:
            stat, p_value = scipy_stats.shapiro(sample)
        except Exception:
            stat, p_value = None, None

        return {
            "skewness": round(float(series.skew()), 4),
            "kurtosis": round(float(series.kurtosis()), 4),
            "shapiro_stat": round(float(stat), 6) if stat is not None else None,
            "shapiro_p": round(float(p_value), 6) if p_value is not None else None,
            "is_normal": bool(p_value > 0.05) if p_value is not None else None,
            "n": len(series),
        }
