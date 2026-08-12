"""Adapter-based export manager."""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

import pandas as pd


class BaseExporter(ABC):
    format_name = ""
    extensions: tuple[str, ...] = ()

    @abstractmethod
    def export(self, df: pd.DataFrame, path: str, **options) -> dict[str, Any]:
        ...

    def validate_path(self, path: str) -> None:
        target = Path(path)
        if not target.parent.exists():
            raise FileNotFoundError(f"La carpeta no existe: {target.parent}")
        if self.extensions and target.suffix.lower() not in self.extensions:
            raise ValueError(f"Extension invalida para {self.format_name}: {target.suffix}")


class CSVExporter(BaseExporter):
    format_name = "csv"
    extensions = (".csv", ".tsv", ".txt")

    def export(self, df: pd.DataFrame, path: str, **options) -> dict[str, Any]:
        self.validate_path(path)
        df.to_csv(path, sep=options.get("separator", ","), encoding=options.get("encoding", "utf-8"), index=False)
        return {"success": True, "path": path, "rows": len(df), "cols": len(df.columns)}


class ExcelExporter(BaseExporter):
    format_name = "excel"
    extensions = (".xlsx", ".xls", ".xlsm", ".ods")

    def export(self, df: pd.DataFrame, path: str, **options) -> dict[str, Any]:
        self.validate_path(path)
        suffix = Path(path).suffix.lower()
        engine = "odf" if suffix == ".ods" else "openpyxl"
        with pd.ExcelWriter(path, engine=engine) as writer:
            df.to_excel(writer, sheet_name=options.get("sheet_name", "Datos"), index=False)
        return {"success": True, "path": path, "rows": len(df), "cols": len(df.columns)}


class JSONExporter(BaseExporter):
    format_name = "json"
    extensions = (".json", ".jsonl", ".ndjson")

    def export(self, df: pd.DataFrame, path: str, **options) -> dict[str, Any]:
        self.validate_path(path)
        lines = options.get("lines", Path(path).suffix.lower() in {".jsonl", ".ndjson"})
        df.to_json(path, orient="records", force_ascii=False, lines=lines, indent=None if lines else 2)
        return {"success": True, "path": path, "rows": len(df), "cols": len(df.columns)}


class XMLExporter(BaseExporter):
    format_name = "xml"
    extensions = (".xml",)

    def export(self, df: pd.DataFrame, path: str, **options) -> dict[str, Any]:
        self.validate_path(path)
        df.to_xml(path, index=False)
        return {"success": True, "path": path, "rows": len(df), "cols": len(df.columns)}


class HTMLExporter(BaseExporter):
    format_name = "html"
    extensions = (".html", ".htm")

    def export(self, df: pd.DataFrame, path: str, **options) -> dict[str, Any]:
        self.validate_path(path)
        df.to_html(path, index=False)
        return {"success": True, "path": path, "rows": len(df), "cols": len(df.columns)}


class YAMLExporter(BaseExporter):
    format_name = "yaml"
    extensions = (".yaml", ".yml")

    def export(self, df: pd.DataFrame, path: str, **options) -> dict[str, Any]:
        self.validate_path(path)
        try:
            import yaml
        except ImportError as exc:
            raise RuntimeError("PyYAML no esta instalado para exportar YAML.") from exc
        with open(path, "w", encoding=options.get("encoding", "utf-8")) as handle:
            yaml.safe_dump(df.to_dict(orient="records"), handle, sort_keys=False, allow_unicode=True)
        return {"success": True, "path": path, "rows": len(df), "cols": len(df.columns)}


class ParquetExporter(BaseExporter):
    format_name = "parquet"
    extensions = (".parquet",)

    def export(self, df: pd.DataFrame, path: str, **options) -> dict[str, Any]:
        self.validate_path(path)
        df.to_parquet(path, index=False)
        return {"success": True, "path": path, "rows": len(df), "cols": len(df.columns)}


class FeatherExporter(BaseExporter):
    format_name = "feather"
    extensions = (".feather", ".arrow")

    def export(self, df: pd.DataFrame, path: str, **options) -> dict[str, Any]:
        self.validate_path(path)
        df.reset_index(drop=True).to_feather(path)
        return {"success": True, "path": path, "rows": len(df), "cols": len(df.columns)}


class ExportManager:
    """Registry for tabular export adapters."""

    def __init__(self):
        self.exporters = {
            "csv": CSVExporter(),
            "tsv": CSVExporter(),
            "txt": CSVExporter(),
            "xlsx": ExcelExporter(),
            "xls": ExcelExporter(),
            "xlsm": ExcelExporter(),
            "ods": ExcelExporter(),
            "json": JSONExporter(),
            "jsonl": JSONExporter(),
            "ndjson": JSONExporter(),
            "xml": XMLExporter(),
            "html": HTMLExporter(),
            "yaml": YAMLExporter(),
            "yml": YAMLExporter(),
            "parquet": ParquetExporter(),
            "feather": FeatherExporter(),
            "arrow": FeatherExporter(),
        }

    def supported_formats(self) -> list[str]:
        return sorted(self.exporters)

    def export_dataframe(self, df: pd.DataFrame, path: str, format_name: str | None = None, **options) -> dict[str, Any]:
        if df is None or df.empty:
            return {"success": False, "error": "No hay datos validos para exportar."}
        fmt = (format_name or Path(path).suffix.lower().lstrip(".")).lower()
        exporter = self.exporters.get(fmt)
        if exporter is None:
            return {"success": False, "error": f"Formato no soportado: {fmt}"}
        if fmt == "tsv":
            options.setdefault("separator", "\t")
        try:
            return exporter.export(df, path, **options)
        except Exception as exc:
            return {"success": False, "error": str(exc)}
