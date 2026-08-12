"""Modular import system with format-specific adapters."""
from __future__ import annotations

from abc import ABC, abstractmethod
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

import pandas as pd
from urllib.request import Request, urlopen
from tempfile import NamedTemporaryFile

from app.core.format_detector import FormatDetector


class _TableParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tables: list[list[list[str]]] = []
        self._table: list[list[str]] | None = None
        self._row: list[str] | None = None
        self._cell: list[str] | None = None

    def handle_starttag(self, tag: str, attrs):
        tag = tag.lower()
        if tag == "table":
            self._table = []
        elif tag == "tr" and self._table is not None:
            self._row = []
        elif tag in {"td", "th"} and self._row is not None:
            self._cell = []

    def handle_data(self, data: str):
        if self._cell is not None:
            self._cell.append(data)

    def handle_endtag(self, tag: str):
        tag = tag.lower()
        if tag in {"td", "th"} and self._cell is not None and self._row is not None:
            self._row.append(" ".join(part.strip() for part in self._cell if part.strip()))
            self._cell = None
        elif tag == "tr" and self._row is not None and self._table is not None:
            if self._row:
                self._table.append(self._row)
            self._row = None
        elif tag == "table" and self._table is not None:
            if self._table:
                self.tables.append(self._table)
            self._table = None


def read_html_tables(file_path: str) -> list[pd.DataFrame]:
    try:
        return pd.read_html(file_path)
    except Exception:
        text = Path(file_path).read_text(encoding="utf-8", errors="ignore")
        parser = _TableParser()
        parser.feed(text)
        frames: list[pd.DataFrame] = []
        for table in parser.tables:
            width = max(len(row) for row in table)
            padded = [row + [""] * (width - len(row)) for row in table]
            if len(padded) > 1 and len(set(padded[0])) == len(padded[0]) and any(padded[0]):
                frames.append(pd.DataFrame(padded[1:], columns=padded[0]))
            else:
                frames.append(pd.DataFrame(padded))
        return frames


class ImporterRegistry:
    """Registry for format adapters to allow future plugin expansion."""

    def __init__(self):
        self._importers: list[BaseImporter] = []

    def register_importer(self, importer: "BaseImporter") -> None:
        if importer not in self._importers:
            self._importers.append(importer)

    def unregister_importer(self, importer: "BaseImporter") -> None:
        self._importers = [item for item in self._importers if item is not importer]

    def list_importers(self) -> list["BaseImporter"]:
        return list(self._importers)

    def supported_formats(self) -> list[str]:
        formats: set[str] = set()
        for importer in self._importers:
            formats.update(getattr(importer, "supported_formats", ()))
        return sorted(formats)

    def get_importer(self, format_name: str) -> "BaseImporter | None":
        for importer in self._importers:
            if importer.can_import(format_name):
                return importer
        return None


class BaseImporter(ABC):
    """Base importer contract for each supported file family."""

    supported_formats: tuple[str, ...] = ()

    @abstractmethod
    def can_import(self, format_name: str) -> bool:
        ...

    @abstractmethod
    def import_data(self, file_path: str, detection: dict[str, Any]) -> pd.DataFrame:
        ...


class CSVImporter(BaseImporter):
    supported_formats = ("csv",)

    def can_import(self, format_name: str) -> bool:
        return format_name in self.supported_formats

    def import_data(self, file_path: str, detection: dict[str, Any]) -> pd.DataFrame:
        separator = detection.get("delimiter", ",")
        return pd.read_csv(file_path, sep=separator, encoding=detection.get("encoding", "utf-8"))


class ExcelImporter(BaseImporter):
    supported_formats = ("excel",)

    def can_import(self, format_name: str) -> bool:
        return format_name in self.supported_formats

    def import_data(self, file_path: str, detection: dict[str, Any]) -> pd.DataFrame:
        return pd.read_excel(file_path)


class DBFImporter(BaseImporter):
    supported_formats = ("dbf",)

    def can_import(self, format_name: str) -> bool:
        return format_name in self.supported_formats

    def import_data(self, file_path: str, detection: dict[str, Any]) -> pd.DataFrame:
        try:
            from dbfread import DBF
        except ImportError as exc:
            raise RuntimeError("dbfread no esta instalado para importar archivos DBF.") from exc
        return pd.DataFrame(iter(DBF(file_path, encoding=detection.get("encoding", "utf-8"))))


class JSONImporter(BaseImporter):
    supported_formats = ("json",)

    def can_import(self, format_name: str) -> bool:
        return format_name in self.supported_formats

    def import_data(self, file_path: str, detection: dict[str, Any]) -> pd.DataFrame:
        path = Path(file_path)
        suffix = path.suffix.lower()
        if suffix in {".jsonl", ".ndjson"}:
            return pd.read_json(file_path, lines=True)
        return pd.read_json(file_path)


class XMLImporter(BaseImporter):
    supported_formats = ("xml",)

    def can_import(self, format_name: str) -> bool:
        return format_name in self.supported_formats

    def import_data(self, file_path: str, detection: dict[str, Any]) -> pd.DataFrame:
        return pd.read_xml(file_path)


class HTMLImporter(BaseImporter):
    supported_formats = ("html",)

    def can_import(self, format_name: str) -> bool:
        return format_name in self.supported_formats

    def import_data(self, file_path: str, detection: dict[str, Any]) -> pd.DataFrame:
        tables = read_html_tables(file_path)
        if not tables:
            raise ValueError("No se encontraron tablas HTML válidas en el archivo.")
        return tables[0]


class ParquetImporter(BaseImporter):
    supported_formats = ("parquet",)

    def can_import(self, format_name: str) -> bool:
        return format_name in self.supported_formats

    def import_data(self, file_path: str, detection: dict[str, Any]) -> pd.DataFrame:
        return pd.read_parquet(file_path)


class FeatherImporter(BaseImporter):
    supported_formats = ("feather",)

    def can_import(self, format_name: str) -> bool:
        return format_name in self.supported_formats

    def import_data(self, file_path: str, detection: dict[str, Any]) -> pd.DataFrame:
        return pd.read_feather(file_path)


class ORCImporter(BaseImporter):
    supported_formats = ("orc",)

    def can_import(self, format_name: str) -> bool:
        return format_name in self.supported_formats

    def import_data(self, file_path: str, detection: dict[str, Any]) -> pd.DataFrame:
        return pd.read_orc(file_path)


class AvroImporter(BaseImporter):
    supported_formats = ("avro",)

    def can_import(self, format_name: str) -> bool:
        return format_name in self.supported_formats

    def import_data(self, file_path: str, detection: dict[str, Any]) -> pd.DataFrame:
        try:
            import fastavro
        except ImportError as exc:
            raise RuntimeError("fastavro no esta instalado para importar Avro.") from exc
        with open(file_path, "rb") as handle:
            return pd.DataFrame(list(fastavro.reader(handle)))


class YAMLImporter(BaseImporter):
    supported_formats = ("yaml",)

    def can_import(self, format_name: str) -> bool:
        return format_name in self.supported_formats

    def import_data(self, file_path: str, detection: dict[str, Any]) -> pd.DataFrame:
        try:
            import yaml

            with open(file_path, "r", encoding=detection.get("encoding", "utf-8")) as handle:
                data = yaml.safe_load(handle)
            if isinstance(data, list):
                return pd.DataFrame(data)
            if isinstance(data, dict):
                return pd.json_normalize(data)
            raise ValueError("El contenido YAML no se pudo convertir a tabla.")
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError("PyYAML no está instalado para importar archivos YAML.") from exc


class TOMLImporter(BaseImporter):
    supported_formats = ("toml",)

    def can_import(self, format_name: str) -> bool:
        return format_name in self.supported_formats

    def import_data(self, file_path: str, detection: dict[str, Any]) -> pd.DataFrame:
        try:
            import tomllib
        except ImportError:  # pragma: no cover
            try:
                import toml as tomllib
            except ImportError as exc:
                raise RuntimeError("tomllib/toml no esta instalado para importar TOML.") from exc
        mode = "rb"
        with open(file_path, mode) as handle:
            data = tomllib.load(handle)
        return pd.json_normalize(data)


class ImportManager:
    """Facade for format-agnostic import."""

    def __init__(self):
        self.registry = ImporterRegistry()
        self._importers = [
            CSVImporter(),
            ExcelImporter(),
            JSONImporter(),
            XMLImporter(),
            HTMLImporter(),
            YAMLImporter(),
            TOMLImporter(),
            DBFImporter(),
        ]
        try:
            import pyarrow  # noqa: F401

            self._importers.append(ParquetImporter())
            self._importers.append(FeatherImporter())
            self._importers.append(ORCImporter())
        except ImportError:
            self._parquet_unavailable = True
        self._importers.append(AvroImporter())
        for importer in self._importers:
            self.registry.register_importer(importer)

    def detect_format(self, file_path: str) -> dict[str, Any]:
        return FormatDetector.detect(file_path)

    def import_file(self, file_path: str, table_index: int | None = None) -> dict[str, Any]:
        if not file_path or not Path(file_path).exists():
            return {"success": False, "error": "El archivo no existe.", "metadata": {"format": "unknown"}}

        if Path(file_path).stat().st_size == 0:
            return {"success": False, "error": "No se pudieron importar datos vacíos.", "metadata": {"format": "unknown"}}

        detection = self.detect_format(file_path)
        importer = self.registry.get_importer(detection["format"])

        if importer is None:
            return {
                "success": False,
                "error": f"Formato no soportado: {detection['format']}",
                "metadata": detection,
            }

        try:
            if detection["format"] == "html":
                html_tables = read_html_tables(file_path)
                if not html_tables:
                    return {"success": False, "error": "No se encontraron tablas HTML válidas.", "metadata": detection}
                selected_index = table_index if table_index is not None else 0
                detection["table_count"] = len(html_tables)
                detection["selected_table_index"] = selected_index
                return {
                    "success": True,
                    "dataframe": html_tables[selected_index],
                    "format": detection["format"],
                    "metadata": detection,
                    "tables": html_tables,
                }

            dataframe = importer.import_data(file_path, detection)
            if dataframe is None or dataframe.empty:
                return {"success": False, "error": "No se pudieron importar datos vacíos.", "metadata": detection}
            return {
                "success": True,
                "dataframe": dataframe,
                "format": detection["format"],
                "metadata": detection,
            }
        except Exception as exc:  # pragma: no cover - surfaced to UI
            return {
                "success": False,
                "error": str(exc),
                "metadata": detection,
            }

    def import_multiple(self, file_paths: list[str]) -> list[dict[str, Any]]:
        results = [self.import_file(path) for path in file_paths]
        valid = [item for item in results if item.get("success")]
        if len(valid) <= 1:
            return results

        frames = [item["dataframe"] for item in valid]
        first_cols = list(frames[0].columns)
        if all(list(frame.columns) == first_cols for frame in frames):
            merged = pd.concat(frames, ignore_index=True)
            return [{"success": True, "dataframe": merged, "merged": True, "metadata": {"format": "multi"}}]
        return results

    def inspect_html_tables(self, file_path: str) -> list[dict[str, Any]]:
        tables = read_html_tables(file_path)
        return [
            {
                "index": idx,
                "rows": len(table),
                "cols": len(table.columns),
                "columns": [str(col) for col in table.columns],
                "nulls": int(table.isna().sum().sum()),
            }
            for idx, table in enumerate(tables)
        ]

    def import_url(self, url: str) -> dict[str, Any]:
        if not url.lower().startswith(("http://", "https://")):
            return {"success": False, "error": "URL no valida.", "metadata": {"format": "unknown"}}
        suffix = Path(url.split("?")[0]).suffix or ".tmp"
        try:
            request = Request(url, headers={"User-Agent": "DataAnalyzerPro/1.0"})
            with urlopen(request, timeout=20) as response:
                payload = response.read()
            if not payload:
                return {"success": False, "error": "La URL no devolvio datos.", "metadata": {"format": "unknown"}}
            with NamedTemporaryFile(delete=False, suffix=suffix) as handle:
                handle.write(payload)
                temp_path = handle.name
            return self.import_file(temp_path)
        except Exception as exc:
            return {"success": False, "error": str(exc), "metadata": {"format": "unknown"}}

    def supported_formats(self) -> list[str]:
        return self.registry.supported_formats()
