import tempfile
import unittest
from pathlib import Path

import pandas as pd

from app.core.ai_manager import AIManager
from app.core.data_manager import DataManager
from app.core.export_manager import ExportManager
from app.core.shortcuts_manager import ShortcutConflictError, ShortcutsManager
from app.core.trash_manager import TrashManager


class CoreManagerTests(unittest.TestCase):
    def test_shortcuts_persist_and_detect_conflicts(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "shortcuts.json"
            shortcuts = ShortcutsManager(path)
            shortcuts.set("new_analysis", "Ctrl+Alt+N")
            self.assertEqual(ShortcutsManager(path).get("new_analysis"), "Ctrl+Alt+N")
            with self.assertRaises(ShortcutConflictError):
                shortcuts.set("export", "Ctrl+O")

    def test_trash_roundtrip_for_payload(self):
        with tempfile.TemporaryDirectory() as tmp:
            trash = TrashManager(tmp)
            item = trash.move_payload_to_trash("dataset", "ventas", {"rows": 3})
            self.assertEqual(len(trash.list_items()), 1)
            payload = trash.restore_payload(item.id)
            self.assertEqual(payload["rows"], 3)
            self.assertEqual(trash.list_items(), [])

    def test_data_manager_restores_dataset_from_trash(self):
        DataManager._instance = None
        dm = DataManager.get_instance()
        dm.trash = TrashManager(tempfile.mkdtemp())
        dm.load_dataframe(pd.DataFrame({"a": [1, 2]}), file_name="demo.csv")
        dm.delete_dataset("demo.csv")
        self.assertEqual(dm.list_datasets(), [])
        item_id = dm.list_trash()[0]["id"]
        restored = dm.restore_from_trash(item_id)
        self.assertEqual(restored, "demo.csv")
        self.assertEqual(len(dm.list_datasets()), 1)
        DataManager._instance = None

    def test_ai_manager_does_not_send_context_without_permission(self):
        dm = DataManager()
        dm.load_dataframe(pd.DataFrame({"amount": [10, None]}), file_name="ventas.csv")
        manager = AIManager()
        self.assertIsNone(manager.build_dataset_context(dm))
        response = manager.ask("Que pasa?", dm)
        self.assertFalse(response.success)
        self.assertEqual(response.provider, "not_configured")

    def test_export_manager_exports_csv_and_rejects_unknown(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "data.csv"
            manager = ExportManager()
            result = manager.export_dataframe(pd.DataFrame({"a": [1]}), str(path), "csv")
            self.assertTrue(result["success"])
            self.assertTrue(path.exists())
            bad = manager.export_dataframe(pd.DataFrame({"a": [1]}), str(Path(tmp) / "data.xyz"), "xyz")
            self.assertFalse(bad["success"])


if __name__ == "__main__":
    unittest.main()
