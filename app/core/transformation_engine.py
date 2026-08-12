"""Core transformation and filtering logic."""
from __future__ import annotations

from typing import Any

import pandas as pd


class TransformationEngine:
    """Applies dataset transformations and keeps logic separate from UI."""

    def __init__(self, data_manager: Any):
        self.dm = data_manager

    def filter_rows(self, column: str, condition: str, value: Any) -> pd.DataFrame:
        df = self.dm.df.copy()
        if column not in df.columns:
            raise ValueError(f"Columna no encontrada: {column}")

        if condition == "==":
            result = df[df[column] == value]
        elif condition == "!=":
            result = df[df[column] != value]
        elif condition == ">":
            result = df[df[column] > value]
        elif condition == ">=":
            result = df[df[column] >= value]
        elif condition == "<":
            result = df[df[column] < value]
        elif condition == "<=":
            result = df[df[column] <= value]
        elif condition == "contains":
            result = df[df[column].astype(str).str.contains(str(value), case=False, na=False)]
        else:
            raise ValueError(f"Condición no soportada: {condition}")

        return result.reset_index(drop=True)

    def sort_values(self, column: str, ascending: bool = True) -> pd.DataFrame:
        df = self.dm.df.copy()
        if column not in df.columns:
            raise ValueError(f"Columna no encontrada: {column}")
        return df.sort_values(by=column, ascending=ascending, na_position="last").reset_index(drop=True)

    def select_columns(self, columns: list[str]) -> pd.DataFrame:
        missing = [col for col in columns if col not in self.dm.df.columns]
        if missing:
            raise ValueError(f"Columnas inexistentes: {missing}")
        return self.dm.df.loc[:, columns].copy()

    def add_calculated_column(self, column_name: str, expression: str) -> pd.DataFrame:
        df = self.dm.df.copy()
        if column_name in df.columns:
            raise ValueError(f"La columna ya existe: {column_name}")
        df[column_name] = df.eval(expression, engine="python")
        return df

    def group_by(self, group_by: list[str], agg: dict[str, str]) -> pd.DataFrame:
        return self.dm.df.groupby(group_by, dropna=False).agg(agg).reset_index()

    def rename_columns(self, mapping: dict[str, str]) -> pd.DataFrame:
        return self.dm.df.rename(columns=mapping)

    def drop_columns(self, columns: list[str]) -> pd.DataFrame:
        return self.dm.df.drop(columns=columns, errors="ignore")

    def drop_rows_by_indices(self, indices: list[int]) -> pd.DataFrame:
        df = self.dm.df.copy()
        valid_indices = [idx for idx in indices if idx in df.index]
        return df.drop(index=valid_indices).reset_index(drop=True)

    def preview_drop_rows_by_condition(self, column: str, condition: str, value: Any) -> pd.DataFrame:
        df = self.dm.df.copy()
        to_keep = self.filter_rows(column, condition, value)
        matched_index = df.index.difference(to_keep.index)
        if condition in {"==", "!=", ">", ">=", "<", "<=", "contains"}:
            if condition == "==":
                mask = df[column] == value
            elif condition == "!=":
                mask = df[column] != value
            elif condition == ">":
                mask = df[column] > value
            elif condition == ">=":
                mask = df[column] >= value
            elif condition == "<":
                mask = df[column] < value
            elif condition == "<=":
                mask = df[column] <= value
            else:
                mask = df[column].astype(str).str.contains(str(value), case=False, na=False)
            return df[mask].copy()
        return df.loc[matched_index].copy()

    def drop_rows_by_condition(self, column: str, condition: str, value: Any) -> pd.DataFrame:
        df = self.dm.df.copy()
        rows_to_drop = self.preview_drop_rows_by_condition(column, condition, value).index
        return df.drop(index=rows_to_drop).reset_index(drop=True)

    def combine_columns(self, source_columns: list[str], new_name: str, separator: str = "") -> pd.DataFrame:
        df = self.dm.df.copy()
        df[new_name] = df[source_columns].fillna("").astype(str).agg(lambda row: separator.join(row), axis=1)
        return df

    def split_column(self, column: str, new_names: list[str], separator: str = ",") -> pd.DataFrame:
        df = self.dm.df.copy()
        parts = df[column].astype(str).str.split(separator, n=len(new_names) - 1, expand=True)
        for idx, name in enumerate(new_names):
            df[name] = parts[idx]
        return df

    def pivot_table(self, index: str, columns: str, values: str, aggfunc: str = "sum") -> pd.DataFrame:
        return self.dm.df.pivot_table(index=index, columns=columns, values=values, aggfunc=aggfunc).reset_index()

    def melt(self, id_vars: list[str], value_vars: list[str]) -> pd.DataFrame:
        return self.dm.df.melt(id_vars=id_vars, value_vars=value_vars)

    def merge(self, other: pd.DataFrame, on: str, how: str = "inner") -> pd.DataFrame:
        return self.dm.df.merge(other, on=on, how=how)
