"""Data cleaning operations."""
import pandas as pd
import numpy as np
from app.core.data_manager import DataManager


class DataCleaner:
    """Provides all data-cleaning operations, each returning a result dict."""

    def __init__(self, data_manager: DataManager):
        self.dm = data_manager

    def _pre_check(self):
        if not self.dm.has_data():
            raise ValueError("No hay datos cargados")

    # ── Duplicates ─────────────────────────────────────────────────────

    def remove_duplicates(self, subset=None, keep="first") -> dict:
        self._pre_check()
        self.dm.save_state()
        before = len(self.dm.df)
        self.dm.df = self.dm.df.drop_duplicates(
            subset=subset, keep=keep
        ).reset_index(drop=True)
        removed = before - len(self.dm.df)
        self.dm.notify()
        return {"removed": removed, "remaining": len(self.dm.df)}

    # ── Missing values ─────────────────────────────────────────────────

    def fill_missing(self, column: str, strategy: str, custom_value=None) -> dict:
        self._pre_check()
        self.dm.save_state()
        missing_before = int(self.dm.df[column].isna().sum())

        if strategy == "mean":
            self.dm.df[column] = self.dm.df[column].fillna(self.dm.df[column].mean())
        elif strategy == "median":
            self.dm.df[column] = self.dm.df[column].fillna(self.dm.df[column].median())
        elif strategy == "mode":
            mode_val = self.dm.df[column].mode()
            if not mode_val.empty:
                self.dm.df[column] = self.dm.df[column].fillna(mode_val.iloc[0])
        elif strategy == "ffill":
            self.dm.df[column] = self.dm.df[column].ffill()
        elif strategy == "bfill":
            self.dm.df[column] = self.dm.df[column].bfill()
        elif strategy == "custom" and custom_value is not None:
            self.dm.df[column] = self.dm.df[column].fillna(custom_value)
        elif strategy == "zero":
            self.dm.df[column] = self.dm.df[column].fillna(0)

        missing_after = int(self.dm.df[column].isna().sum())
        self.dm.notify()
        return {
            "column": column,
            "filled": missing_before - missing_after,
            "remaining": missing_after,
        }

    def drop_missing_rows(self, threshold: float = 0.5) -> dict:
        self._pre_check()
        self.dm.save_state()
        before = len(self.dm.df)
        min_count = int(threshold * len(self.dm.df.columns))
        self.dm.df = self.dm.df.dropna(thresh=min_count).reset_index(drop=True)
        dropped = before - len(self.dm.df)
        self.dm.notify()
        return {"dropped": dropped, "remaining": len(self.dm.df)}

    def drop_missing_columns(self, threshold: float = 0.5) -> dict:
        self._pre_check()
        self.dm.save_state()
        before_cols = list(self.dm.df.columns)
        min_count = int(threshold * len(self.dm.df))
        self.dm.df = self.dm.df.dropna(axis=1, thresh=min_count)
        dropped_cols = [c for c in before_cols if c not in self.dm.df.columns]
        self.dm.notify()
        return {"dropped": len(dropped_cols), "columns": dropped_cols}

    def drop_column(self, column: str) -> dict:
        self._pre_check()
        self.dm.save_state()
        self.dm.df = self.dm.df.drop(columns=[column])
        self.dm.notify()
        return {"dropped": column, "remaining_cols": len(self.dm.df.columns)}

    # ── Type conversion ────────────────────────────────────────────────

    def convert_type(self, column: str, target_type: str) -> dict:
        self._pre_check()
        self.dm.save_state()
        original_type = str(self.dm.df[column].dtype)
        try:
            if target_type == "numeric":
                self.dm.df[column] = pd.to_numeric(
                    self.dm.df[column], errors="coerce"
                )
            elif target_type == "string":
                self.dm.df[column] = self.dm.df[column].astype(str)
            elif target_type == "datetime":
                self.dm.df[column] = pd.to_datetime(
                    self.dm.df[column], errors="coerce"
                )
            elif target_type == "category":
                self.dm.df[column] = self.dm.df[column].astype("category")
            elif target_type == "integer":
                self.dm.df[column] = pd.to_numeric(
                    self.dm.df[column], errors="coerce"
                ).astype("Int64")
            elif target_type == "float":
                self.dm.df[column] = pd.to_numeric(
                    self.dm.df[column], errors="coerce"
                ).astype("float64")
        except Exception as e:
            self.dm.undo()
            return {"success": False, "error": str(e)}

        self.dm.notify()
        return {
            "success": True,
            "column": column,
            "from": original_type,
            "to": str(self.dm.df[column].dtype),
        }

    # ── Column rename ──────────────────────────────────────────────────

    def rename_column(self, old_name: str, new_name: str) -> dict:
        self._pre_check()
        self.dm.save_state()
        self.dm.df = self.dm.df.rename(columns={old_name: new_name})
        self.dm.notify()
        return {"from": old_name, "to": new_name}

    # ── Outliers ───────────────────────────────────────────────────────

    def remove_outliers(
        self, column: str, method: str = "iqr", factor: float = 1.5
    ) -> dict:
        self._pre_check()
        if not pd.api.types.is_numeric_dtype(self.dm.df[column]):
            return {"success": False, "error": "La columna no es numérica"}

        self.dm.save_state()
        before = len(self.dm.df)

        if method == "iqr":
            q1 = self.dm.df[column].quantile(0.25)
            q3 = self.dm.df[column].quantile(0.75)
            iqr = q3 - q1
            lower = q1 - factor * iqr
            upper = q3 + factor * iqr
            mask = (self.dm.df[column] >= lower) & (self.dm.df[column] <= upper)
        elif method == "zscore":
            from scipy import stats

            col_clean = self.dm.df[column].dropna()
            z = np.abs(stats.zscore(col_clean))
            full_z = pd.Series(np.nan, index=self.dm.df.index)
            full_z.loc[col_clean.index] = z
            mask = full_z.abs() <= factor
            mask = mask.fillna(True)
        else:
            return {"success": False, "error": f"Método desconocido: {method}"}

        self.dm.df = self.dm.df[mask].reset_index(drop=True)
        removed = before - len(self.dm.df)
        self.dm.notify()
        return {"success": True, "removed": removed, "remaining": len(self.dm.df)}

    # ── Whitespace ─────────────────────────────────────────────────────

    def strip_whitespace(self) -> dict:
        self._pre_check()
        self.dm.save_state()
        str_cols = self.dm.df.select_dtypes(include=["object"]).columns
        for col in str_cols:
            self.dm.df[col] = self.dm.df[col].str.strip()
        self.dm.df.columns = [c.strip() for c in self.dm.df.columns]
        self.dm.notify()
        return {"columns_cleaned": len(str_cols)}
