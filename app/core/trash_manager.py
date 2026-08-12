"""Persistent trash bin for recoverable application items."""
from __future__ import annotations

import json
import shutil
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class TrashItem:
    id: str
    item_type: str
    name: str
    original_location: str
    trash_location: str
    deleted_at: str
    metadata: dict[str, Any]


class TrashManager:
    """Stores deleted items until the user restores or purges them."""

    def __init__(self, root_path: str | Path | None = None):
        base = Path(root_path) if root_path else Path(__file__).resolve().parents[1] / "trash"
        self.root_path = base
        self.items_path = self.root_path / "trash.json"
        self.root_path.mkdir(parents=True, exist_ok=True)

    def _load(self) -> list[TrashItem]:
        if not self.items_path.exists():
            return []
        try:
            data = json.loads(self.items_path.read_text(encoding="utf-8"))
            return [TrashItem(**item) for item in data]
        except Exception:
            return []

    def _save(self, items: list[TrashItem]) -> None:
        self.root_path.mkdir(parents=True, exist_ok=True)
        self.items_path.write_text(json.dumps([asdict(item) for item in items], indent=2), encoding="utf-8")

    def list_items(self) -> list[dict[str, Any]]:
        return [asdict(item) for item in self._load()]

    def move_payload_to_trash(
        self,
        item_type: str,
        name: str,
        payload: Any,
        original_location: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> TrashItem:
        item_id = f"{datetime.now().strftime('%Y%m%d%H%M%S%f')}_{item_type}_{self._safe_name(name)}"
        trash_location = self.root_path / f"{item_id}.pkl"
        try:
            import pickle

            with open(trash_location, "wb") as handle:
                pickle.dump(payload, handle)
        except Exception as exc:
            raise RuntimeError(f"No se pudo mover '{name}' a la papelera: {exc}") from exc

        item = TrashItem(
            id=item_id,
            item_type=item_type,
            name=name,
            original_location=original_location,
            trash_location=str(trash_location),
            deleted_at=datetime.now().isoformat(timespec="seconds"),
            metadata=metadata or {},
        )
        items = self._load()
        items.append(item)
        self._save(items)
        return item

    def move_path_to_trash(self, path: str | Path, item_type: str = "file", metadata: dict[str, Any] | None = None) -> TrashItem:
        source = Path(path)
        if not source.exists():
            raise FileNotFoundError(f"No existe: {source}")
        item_id = f"{datetime.now().strftime('%Y%m%d%H%M%S%f')}_{item_type}_{self._safe_name(source.name)}"
        target = self.root_path / item_id
        if source.is_dir():
            shutil.move(str(source), str(target))
        else:
            target = target.with_suffix(source.suffix)
            shutil.move(str(source), str(target))
        item = TrashItem(
            id=item_id,
            item_type=item_type,
            name=source.name,
            original_location=str(source),
            trash_location=str(target),
            deleted_at=datetime.now().isoformat(timespec="seconds"),
            metadata=metadata or {},
        )
        items = self._load()
        items.append(item)
        self._save(items)
        return item

    def restore_payload(self, item_id: str) -> Any:
        item = self._find(item_id)
        if item is None:
            raise ValueError(f"Elemento de papelera no encontrado: {item_id}")
        try:
            import pickle

            with open(item.trash_location, "rb") as handle:
                payload = pickle.load(handle)
        except Exception as exc:
            raise RuntimeError(f"No se pudo restaurar '{item.name}': {exc}") from exc
        self._remove_record(item_id, delete_file=True)
        return payload

    def restore_path(self, item_id: str, target_location: str | Path | None = None) -> Path:
        item = self._find(item_id)
        if item is None:
            raise ValueError(f"Elemento de papelera no encontrado: {item_id}")
        target = Path(target_location or item.original_location)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(item.trash_location, str(target))
        self._remove_record(item_id, delete_file=False)
        return target

    def delete_permanently(self, item_id: str) -> None:
        if self._find(item_id) is None:
            raise ValueError(f"Elemento de papelera no encontrado: {item_id}")
        self._remove_record(item_id, delete_file=True)

    def empty(self) -> int:
        items = self._load()
        for item in items:
            self._delete_location(Path(item.trash_location))
        self._save([])
        return len(items)

    def _find(self, item_id: str) -> TrashItem | None:
        return next((item for item in self._load() if item.id == item_id), None)

    def _remove_record(self, item_id: str, delete_file: bool) -> None:
        items = self._load()
        remaining = []
        for item in items:
            if item.id == item_id:
                if delete_file:
                    self._delete_location(Path(item.trash_location))
            else:
                remaining.append(item)
        self._save(remaining)

    @staticmethod
    def _delete_location(path: Path) -> None:
        if path.is_dir():
            shutil.rmtree(path)
        elif path.exists():
            path.unlink()

    @staticmethod
    def _safe_name(name: str) -> str:
        return "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in name)[:80] or "item"
