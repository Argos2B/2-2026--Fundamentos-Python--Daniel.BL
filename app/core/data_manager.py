"""Central data management with singleton pattern and observer callbacks."""
import os
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Callable, Any

import pandas as pd

from app.core.history_manager import HistoryManager
from app.core.ohlc_detector import detect_ohlc
from app.core.trash_manager import TrashManager

LOGGER = logging.getLogger(__name__)


@dataclass
class DatasetRecord:
    name: str
    dataframe: pd.DataFrame
    file_path: str | None = None
    imported_at: str = ""
    format: str = "dataframe"

    def info(self) -> dict[str, Any]:
        mem = int(self.dataframe.memory_usage(deep=True).sum())
        return {
            "name": self.name,
            "rows": len(self.dataframe),
            "cols": len(self.dataframe.columns),
            "memory_bytes": mem,
            "format": self.format,
            "file_path": self.file_path or "",
            "imported_at": self.imported_at,
        }


class DataManager:
    """Singleton that holds the active DataFrame and notifies observers on change."""

    _instance: Optional["DataManager"] = None
    MAX_HISTORY = 20

    def __init__(self):
        self.df: Optional[pd.DataFrame] = None
        self.original_df: Optional[pd.DataFrame] = None
        self.file_path: Optional[str] = None
        self.file_name: Optional[str] = None
        self.ohlc_metadata: dict[str, Any] = {}
        self._callbacks: list[Callable] = []
        self.history = HistoryManager()
        self.datasets: dict[str, DatasetRecord] = {}
        self.current_project: str | None = None
        self.analysis_sessions: list[dict[str, Any]] = []
        self.created_charts: list[dict[str, Any]] = []
        self.trash = TrashManager()

    @classmethod
    def get_instance(cls) -> "DataManager":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    # ── I/O ────────────────────────────────────────────────────────────

    def load_dataframe(
        self,
        dataframe: pd.DataFrame,
        file_name: str | None = None,
        file_path: str | None = None,
    ) -> dict[str, Any]:
        """Store a DataFrame as active dataset and notify observers."""
        self.df = dataframe.copy()
        self.original_df = dataframe.copy()
        self.file_name = file_name or os.path.basename(file_path) if file_path else file_name or "dataset"
        self.file_path = file_path
        self.ohlc_metadata = detect_ohlc(self.df)
        self.history.clear()
        self._register_dataset(self.file_name, self.df, file_path=file_path)
        self.history.record_snapshot(self.df.copy(), self.file_name or "dataset", "Importar dataset")
        self.notify()
        return self.get_info()

    def _register_dataset(
        self,
        name: str,
        dataframe: pd.DataFrame,
        file_path: str | None = None,
        format_name: str | None = None,
    ) -> None:
        base = name or "dataset"
        final_name = base
        counter = 2
        while final_name in self.datasets and self.datasets[final_name].file_path != file_path:
            final_name = f"{base} ({counter})"
            counter += 1
        self.datasets[final_name] = DatasetRecord(
            name=final_name,
            dataframe=dataframe.copy(),
            file_path=file_path,
            imported_at=datetime.now().isoformat(timespec="seconds"),
            format=format_name or (os.path.splitext(base)[1].lstrip(".") or "dataframe"),
        )

    def load_csv(
        self,
        path: str,
        encoding: str = "utf-8",
        separator: str = ",",
        header: int = 0,
    ) -> dict[str, Any]:
        """Load a CSV file and return a summary dict."""
        dataframe = pd.read_csv(path, encoding=encoding, sep=separator, header=header)
        return self.load_dataframe(dataframe, file_name=os.path.basename(path), file_path=path)

    def load_file(self, path: str, detection: dict[str, Any] | None = None) -> dict[str, Any]:
        """Load a file through the format detection/import manager logic."""
        from app.core.import_manager import ImportManager

        manager = ImportManager()
        result = manager.import_file(path)
        if not result.get("success"):
            raise ValueError(result.get("error", "No se pudo importar el archivo."))
        return self.load_dataframe(
            result["dataframe"],
            file_name=os.path.basename(path),
            file_path=path,
        )

    # ── State management ───────────────────────────────────────────────

    def has_data(self) -> bool:
        return self.df is not None and not self.df.empty

    def is_ohlc(self) -> bool:
        return bool(self.ohlc_metadata.get("is_ohlc"))

    def get_ohlc_metadata(self) -> dict[str, Any]:
        return self.ohlc_metadata.copy()

    def get_info(self) -> dict[str, Any]:
        if not self.has_data():
            return {}
        mem = self.df.memory_usage(deep=True).sum()
        if mem < 1024:
            mem_str = f"{mem} B"
        elif mem < 1024 ** 2:
            mem_str = f"{mem / 1024:.1f} KB"
        else:
            mem_str = f"{mem / (1024 ** 2):.1f} MB"
        return {
            "rows": len(self.df),
            "cols": len(self.df.columns),
            "columns": list(self.df.columns),
            "dtypes": {col: str(dt) for col, dt in self.df.dtypes.items()},
            "memory": mem_str,
            "file_name": self.file_name or "N/A",
        }

    def get_shape_str(self) -> str:
        if not self.has_data():
            return "Sin datos"
        info = self.get_info()
        return (
            f"{info['file_name']}  •  "
            f"{info['rows']:,} filas × {info['cols']} columnas  •  "
            f"{info['memory']}"
        )

    # ── History (undo) ─────────────────────────────────────────────────

    def save_state(self):
        """Push current DataFrame to history stack."""
        if self.df is not None:
            self.history.record_snapshot(self.df.copy(), self.file_name or "dataset", "state")

    def apply_dataframe(self, dataframe: pd.DataFrame, action: str) -> dict[str, Any]:
        """Apply a transformed dataframe, preserving undo/redo and dataset state."""
        if self.df is None:
            raise ValueError("No hay datos cargados")
        self.save_state()
        self.df = dataframe.copy()
        self.ohlc_metadata = detect_ohlc(self.df)
        if self.file_name:
            self._register_dataset(self.file_name, self.df, self.file_path)
        self.history.record_snapshot(self.df.copy(), self.file_name or "dataset", action)
        self.notify()
        return self.get_info()

    def commit_state(self, action: str) -> None:
        if self.df is not None:
            self.history.record_snapshot(self.df.copy(), self.file_name or "dataset", action)

    def undo(self) -> bool:
        """Restore previous state. Returns True on success."""
        last_entry = self.history.undo()
        if last_entry is not None:
            self.df = last_entry.dataframe.copy()
            self.ohlc_metadata = detect_ohlc(self.df)
            self.notify()
            return True
        return False

    def redo(self) -> bool:
        entry = self.history.redo()
        if entry is not None:
            self.df = entry.dataframe.copy()
            self.ohlc_metadata = detect_ohlc(self.df)
            self.notify()
            return True
        return False

    def reset(self):
        """Reset to the originally loaded data."""
        if self.original_df is not None:
            self.save_state()
            self.df = self.original_df.copy()
            self.notify()

    def can_undo(self) -> bool:
        return bool(self.history.entries())

    def list_datasets(self) -> list[dict[str, Any]]:
        return [record.info() for record in self.datasets.values()]

    def open_dataset(self, name: str) -> dict[str, Any]:
        if name not in self.datasets:
            raise ValueError(f"Dataset no encontrado: {name}")
        record = self.datasets[name]
        self.df = record.dataframe.copy()
        self.original_df = record.dataframe.copy()
        self.file_name = record.name
        self.file_path = record.file_path
        self.ohlc_metadata = detect_ohlc(self.df)
        self.history.record_snapshot(self.df.copy(), self.file_name, "Abrir dataset")
        self.notify()
        return self.get_info()

    def rename_dataset(self, old_name: str, new_name: str) -> None:
        if old_name not in self.datasets:
            raise ValueError(f"Dataset no encontrado: {old_name}")
        if not new_name.strip():
            raise ValueError("El nombre no puede estar vacio")
        record = self.datasets.pop(old_name)
        record.name = new_name.strip()
        self.datasets[record.name] = record
        if self.file_name == old_name:
            self.file_name = record.name
        self.notify()

    def duplicate_dataset(self, name: str) -> str:
        if name not in self.datasets:
            raise ValueError(f"Dataset no encontrado: {name}")
        record = self.datasets[name]
        copy_name = f"{name} copia"
        counter = 2
        while copy_name in self.datasets:
            copy_name = f"{name} copia {counter}"
            counter += 1
        self._register_dataset(copy_name, record.dataframe, record.file_path, record.format)
        self.notify()
        return copy_name

    def delete_dataset(self, name: str, permanent: bool = False) -> None:
        if name not in self.datasets:
            raise ValueError(f"Dataset no encontrado: {name}")
        record = self.datasets.pop(name)
        if not permanent:
            self.trash.move_payload_to_trash(
                "dataset",
                name,
                record,
                original_location=record.file_path or "session",
                metadata=record.info(),
            )
        if self.file_name == name:
            self.df = None
            self.original_df = None
            self.file_name = None
            self.file_path = None
        self.notify()

    def list_trash(self) -> list[dict[str, Any]]:
        return self.trash.list_items()

    def restore_from_trash(self, item_id: str) -> str:
        payload = self.trash.restore_payload(item_id)
        if isinstance(payload, DatasetRecord):
            name = payload.name
            counter = 2
            while name in self.datasets:
                name = f"{payload.name} restaurado {counter}"
                counter += 1
            payload.name = name
            self.datasets[name] = payload
            self.notify()
            return name
        raise ValueError("El elemento seleccionado no es un dataset restaurable.")

    def delete_trash_item_permanently(self, item_id: str) -> None:
        self.trash.delete_permanently(item_id)
        self.notify()

    def empty_trash(self) -> int:
        removed = self.trash.empty()
        self.notify()
        return removed

    def new_analysis_session(self) -> dict[str, Any]:
        if not self.has_data():
            raise ValueError("Carga un dataset antes de iniciar un analisis")
        session = {
            "id": len(self.analysis_sessions) + 1,
            "dataset": self.file_name or "dataset",
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "rows": len(self.df),
            "cols": len(self.df.columns),
        }
        self.analysis_sessions.append(session)
        self.history.record_snapshot(self.df.copy(), session["dataset"], "Nuevo analisis")
        return session

    def save_chart(self, chart_config: dict[str, Any]) -> dict[str, Any]:
        chart = {
            "id": f"chart_{len(self.created_charts) + 1}",
            "dataset": self.file_name or "dataset",
            "created_at": datetime.now().isoformat(timespec="seconds"),
            **chart_config,
        }
        self.created_charts.append(chart)
        self.notify()
        return chart

    def duplicate_chart(self, chart_id: str) -> dict[str, Any]:
        chart = next((item for item in self.created_charts if item.get("id") == chart_id), None)
        if chart is None:
            raise ValueError(f"Grafico no encontrado: {chart_id}")
        duplicate = chart.copy()
        duplicate["id"] = f"chart_{len(self.created_charts) + 1}"
        duplicate["title"] = f"{chart.get('title', chart_id)} copia"
        duplicate["created_at"] = datetime.now().isoformat(timespec="seconds")
        self.created_charts.append(duplicate)
        self.notify()
        return duplicate

    def delete_chart(self, chart_id: str, permanent: bool = False) -> None:
        chart = next((item for item in self.created_charts if item.get("id") == chart_id), None)
        if chart is None:
            raise ValueError(f"Grafico no encontrado: {chart_id}")
        self.created_charts = [item for item in self.created_charts if item.get("id") != chart_id]
        if not permanent:
            self.trash.move_payload_to_trash("chart", chart.get("title", chart_id), chart, metadata=chart)
        self.notify()

    # ── Observer pattern ───────────────────────────────────────────────

    def add_callback(self, callback: Callable):
        if callback not in self._callbacks:
            self._callbacks.append(callback)

    def remove_callback(self, callback: Callable):
        self._callbacks = [cb for cb in self._callbacks if cb != callback]

    def notify(self):
        for cb in self._callbacks:
            try:
                cb()
            except Exception as exc:
                LOGGER.exception("DataManager callback failed: %s", exc)
