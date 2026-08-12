"""Automatic file format detection for imports."""
from __future__ import annotations

import csv
import json
import mimetypes
from pathlib import Path
from typing import Any


class FormatDetector:
    """Detects format, encoding, delimiter and confidence level."""

    EXTENSION_MAP = {
        ".csv": "csv",
        ".tsv": "csv",
        ".txt": "csv",
        ".xlsx": "excel",
        ".xls": "excel",
        ".xlsm": "excel",
        ".xlsb": "excel",
        ".ods": "excel",
        ".dbf": "dbf",
        ".json": "json",
        ".jsonl": "json",
        ".ndjson": "json",
        ".xml": "xml",
        ".yaml": "yaml",
        ".yml": "yaml",
        ".toml": "toml",
        ".html": "html",
        ".htm": "html",
        ".parquet": "parquet",
        ".feather": "feather",
        ".arrow": "feather",
        ".orc": "orc",
        ".avro": "avro",
    }

    @staticmethod
    def detect(path: str, sample_size: int = 65536) -> dict[str, Any]:
        file_path = Path(path)
        suffix = file_path.suffix.lower()
        extension_format = FormatDetector.EXTENSION_MAP.get(suffix)
        mime_type = mimetypes.guess_type(str(file_path))[0] or "application/octet-stream"

        result: dict[str, Any] = {
            "format": extension_format or "unknown",
            "encoding": "utf-8",
            "delimiter": ",",
            "confidence": 0.9 if extension_format else 0.4,
            "extension": suffix,
            "mime_type": mime_type,
            "file_size": file_path.stat().st_size if file_path.exists() else 0,
        }

        if not file_path.exists():
            return result

        try:
            with open(file_path, "rb") as handle:
                sample = handle.read(sample_size)
        except OSError:
            return result

        encoding = FormatDetector._detect_encoding(sample)
        if encoding:
            result["encoding"] = encoding

        text_sample = sample.decode(encoding, errors="ignore")
        if extension_format in {"csv", "json", "xml", "html", "yaml", "toml"}:
            result.update(FormatDetector._detect_structure(text_sample, extension_format, suffix))

        return result

    @staticmethod
    def _detect_encoding(sample: bytes) -> str:
        for encoding in ("utf-8-sig", "utf-8", "utf-16", "cp1252", "latin-1"):
            try:
                sample.decode(encoding)
                return encoding
            except UnicodeDecodeError:
                continue
        return "utf-8"

    @staticmethod
    def _detect_structure(text_sample: str, extension_format: str, suffix: str) -> dict[str, Any]:
        detection: dict[str, Any] = {}

        if extension_format == "csv":
            delimiter = ","
            try:
                dialect = csv.Sniffer().sniff(text_sample[:4096], delimiters=",;\t|")
                delimiter = dialect.delimiter
            except csv.Error:
                delimiter = "\t" if "\t" in text_sample else delimiter
            detection["delimiter"] = delimiter
            detection["confidence"] = 0.95 if delimiter in {",", ";", "\t", "|"} else 0.75

        elif extension_format == "json":
            try:
                json.loads(text_sample)
                detection["confidence"] = 0.96
            except json.JSONDecodeError:
                detection["confidence"] = 0.65

        elif extension_format == "xml":
            detection["confidence"] = 0.9 if "<" in text_sample and ">" in text_sample else 0.6

        elif extension_format == "html":
            detection["confidence"] = 0.92 if "<table" in text_sample.lower() or "<html" in text_sample.lower() else 0.7

        elif extension_format in {"yaml", "toml"}:
            detection["confidence"] = 0.8

        if suffix in {".tsv", ".txt"} and detection.get("delimiter") == ",":
            detection["delimiter"] = "\t" if "\t" in text_sample else ","

        return detection
