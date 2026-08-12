"""Persistent keyboard shortcut registry."""
from __future__ import annotations

import json
from pathlib import Path


class ShortcutConflictError(ValueError):
    def __init__(self, shortcut: str, assigned_action: str):
        super().__init__(f"El atajo {shortcut} ya esta asignado a: {assigned_action}")
        self.shortcut = shortcut
        self.assigned_action = assigned_action


class ShortcutsManager:
    DEFAULTS = {
        "open": "Ctrl+O",
        "import": "Ctrl+I",
        "save": "Ctrl+S",
        "export": "Ctrl+E",
        "undo": "Ctrl+Z",
        "redo": "Ctrl+Y",
        "search": "Ctrl+F",
        "new_analysis": "Ctrl+N",
        "open_project": "Ctrl+Shift+O",
    }

    def __init__(self, storage_path: str | Path | None = None):
        self.storage_path = Path(storage_path) if storage_path else Path(__file__).resolve().parents[1] / "shortcuts.json"
        self._shortcuts = self.DEFAULTS.copy()
        self.load()

    def load(self) -> dict[str, str]:
        if self.storage_path.exists():
            try:
                data = json.loads(self.storage_path.read_text(encoding="utf-8"))
                self._shortcuts = {**self.DEFAULTS, **data}
            except Exception:
                self._shortcuts = self.DEFAULTS.copy()
        return self.all()

    def save(self) -> None:
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.storage_path.write_text(json.dumps(self._shortcuts, indent=2), encoding="utf-8")

    def all(self) -> dict[str, str]:
        return self._shortcuts.copy()

    def get(self, action: str) -> str:
        return self._shortcuts[action]

    def set(self, action: str, shortcut: str) -> None:
        if action not in self.DEFAULTS:
            raise KeyError(f"Accion desconocida: {action}")
        normalized = self.normalize(shortcut)
        conflict = self.find_conflict(action, normalized)
        if conflict:
            raise ShortcutConflictError(normalized, conflict)
        self._shortcuts[action] = normalized
        self.save()

    def reset(self, action: str) -> None:
        self._shortcuts[action] = self.DEFAULTS[action]
        self.save()

    def reset_all(self) -> None:
        self._shortcuts = self.DEFAULTS.copy()
        self.save()

    def find_conflict(self, action: str, shortcut: str) -> str | None:
        normalized = self.normalize(shortcut)
        for key, value in self._shortcuts.items():
            if key != action and self.normalize(value) == normalized:
                return key
        return None

    @staticmethod
    def normalize(shortcut: str) -> str:
        parts = [part.strip() for part in shortcut.replace("-", "+").split("+") if part.strip()]
        order = {"Ctrl": 0, "Control": 0, "Alt": 1, "Shift": 2}
        canonical: list[str] = []
        for part in parts:
            lower = part.lower()
            if lower in {"ctrl", "control"}:
                canonical.append("Ctrl")
            elif lower == "alt":
                canonical.append("Alt")
            elif lower == "shift":
                canonical.append("Shift")
            else:
                canonical.append(part.upper() if len(part) == 1 else part)
        modifiers = sorted([p for p in canonical if p in order], key=lambda p: order[p])
        keys = [p for p in canonical if p not in order]
        if not keys:
            raise ValueError("El atajo debe incluir una tecla principal")
        return "+".join(modifiers + keys)

    @staticmethod
    def to_tk_sequence(shortcut: str) -> str:
        parts = ShortcutsManager.normalize(shortcut).split("+")
        key = parts[-1]
        modifiers = parts[:-1]
        tk_mods = ["Control" if mod == "Ctrl" else mod for mod in modifiers]
        return "<" + "-".join(tk_mods + [key.lower() if len(key) == 1 else key]) + ">"
