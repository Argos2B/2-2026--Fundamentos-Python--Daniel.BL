"""Central data management with singleton pattern and observer callbacks."""
import os
import pandas as pd
from typing import Optional, Callable, Any
class DataManager:
    """Singleton that holds the active DataFrame and notifies observers on change."""
    _instance: Optional["DataManager"] = None
    MAX_HISTORY = 20
    def __init__(self):
        self.df: Optional[pd.DataFrame] = None
        self.original_df: Optional[pd.DataFrame] = None
        self.file_path: Optional[str] = None
        self.file_name: Optional[str] = None
        self._callbacks: list[Callable] = []
        self._history: list[pd.DataFrame] = []
    @classmethod
    def get_instance(cls) -> "DataManager":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    # ── I/O ────────────────────────────────────────────────────────────
    def load_csv(
        self,
        path: str,
        encoding: str = "utf-8",
        separator: str = ",",
        header: int = 0,
    ) -> dict[str, Any]:
        """Load a CSV file and return a summary dict."""
        self.df = pd.read_csv(path, encoding=encoding, sep=separator, header=header)
        self.original_df = self.df.copy()
        self.file_path = path
        self.file_name = os.path.basename(path)
        self._history.clear()
        self.notify()
        return self.get_info()
    # ── State management ───────────────────────────────────────────────
    def has_data(self) -> bool:
        return self.df is not None and not self.df.empty
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
            if len(self._history) >= self.MAX_HISTORY:
                self._history.pop(0)
            self._history.append(self.df.copy())
    def undo(self) -> bool:
        """Restore previous state. Returns True on success."""
        if self._history:
            self.df = self._history.pop()
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
        return len(self._history) > 0
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
            except Exception:
                pass
