import os
import tempfile
import unittest

import pandas as pd

from app.core.auth_manager import AuthManager
from app.core.cleaner import DataCleaner
from app.core.history_manager import HistoryManager
from app.core.settings_manager import SettingsManager
from app.core.transformation_engine import TransformationEngine


class Phase3CoreTests(unittest.TestCase):
    def setUp(self):
        self.df = pd.DataFrame({
            "customer": ["Ana", "Ana", "Luis", "Maria", "Maria"],
            "age": [30, 30, 28, None, 35],
            "price": [120.0, 120.0, 80.0, 90.0, 200.0],
            "city": ["San Jose", "San Jose", "Heredia", "", "Alajuela"],
        })

    def test_cleaner_removes_duplicates_and_nulls(self):
        dm = type("DM", (), {"df": self.df.copy(), "save_state": lambda self: None, "notify": lambda self: None})()
        cleaner = DataCleaner(dm)
        result = cleaner.remove_duplicates()
        self.assertEqual(result["removed"], 1)
        self.assertEqual(len(dm.df), 4)

        fill_result = cleaner.fill_missing("age", "median")
        self.assertEqual(fill_result["filled"], 1)

    def test_transformation_filter_and_sort(self):
        dm = type("DM", (), {"df": self.df.copy(), "save_state": lambda self: None, "notify": lambda self: None})()
        engine = TransformationEngine(dm)
        filtered = engine.filter_rows("price", ">", 100)
        self.assertEqual(len(filtered), 3)
        sorted_df = engine.sort_values("age", ascending=False)
        self.assertEqual(sorted_df.iloc[0]["age"], 35.0)

    def test_history_manager_tracks_undo_redo(self):
        manager = HistoryManager()
        history = [self.df.copy(), self.df.copy().head(3)]
        manager.record_snapshot(history[0], "import")
        manager.record_snapshot(history[1], "filter")
        undone = manager.undo()
        self.assertIsNotNone(undone)
        redone = manager.redo()
        self.assertIsNotNone(redone)

    def test_settings_manager_persists_preferences(self):
        path = os.path.join(tempfile.gettempdir(), "dap_settings_test.json")
        if os.path.exists(path):
            os.remove(path)

        settings = SettingsManager(path)
        settings.set("theme", "dark")
        settings.set("show_recent_files", True)
        loaded = SettingsManager(path)
        self.assertEqual(loaded.get("theme"), "dark")
        self.assertTrue(loaded.get("show_recent_files"))

        os.remove(path)

    def test_auth_manager_reports_pending_oauth(self):
        manager = AuthManager()
        state = manager.get_status()
        self.assertEqual(state["state"], "logged_out")
        oauth = manager.start_oauth()
        self.assertEqual(oauth["state"], "authentication_error")
        self.assertIn("Client ID", oauth["message"])


if __name__ == "__main__":
    unittest.main()
