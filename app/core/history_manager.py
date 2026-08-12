"""History and undo/redo state manager."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pandas as pd


@dataclass
class HistoryEntry:
    label: str
    dataframe: pd.DataFrame
    action: str = ""


class HistoryManager:
    """Tracks dataset snapshots for undo/redo operations."""

    def __init__(self):
        self._past: list[HistoryEntry] = []
        self._future: list[HistoryEntry] = []

    def record_snapshot(self, dataframe: pd.DataFrame, label: str, action: str = "") -> None:
        self._past.append(HistoryEntry(label=label, dataframe=dataframe.copy(), action=action))
        if len(self._past) > 50:
            self._past.pop(0)
        self._future.clear()

    def undo(self) -> HistoryEntry | None:
        if not self._past:
            return None
        current = self._past.pop()
        self._future.append(current)
        if not self._past:
            return current
        return self._past[-1]

    def redo(self) -> HistoryEntry | None:
        if not self._future:
            return None
        next_entry = self._future.pop()
        self._past.append(next_entry)
        return next_entry

    def clear(self) -> None:
        self._past.clear()
        self._future.clear()

    def entries(self) -> list[HistoryEntry]:
        return list(self._past)
