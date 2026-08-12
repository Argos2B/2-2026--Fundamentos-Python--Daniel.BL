import os
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from app.core.cleaner import DataCleaner
from app.core.data_manager import DataManager
from app.core.exporter import DataExporter
from app.core.import_manager import ImportManager
from app.core.project_manager import ProjectManager
from app.core.settings_manager import SettingsManager
from app.core.transformation_engine import TransformationEngine


class FunctionalFlowTests(unittest.TestCase):
    def setUp(self):
        DataManager._instance = None
        self.dm = DataManager.get_instance()
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.df = pd.DataFrame(
            {
                "name": ["Ana", "Luis", "Ana", None],
                "amount": [10, 20, 10, 40],
                "city": ["San Jose", "Heredia", "San Jose", "Cartago"],
            }
        )

    def tearDown(self):
        self.tmp.cleanup()
        DataManager._instance = None

    def test_import_csv_json_html_xlsx(self):
        csv_path = self.root / "data.csv"
        json_path = self.root / "data.json"
        html_path = self.root / "data.html"
        xlsx_path = self.root / "data.xlsx"
        self.df.to_csv(csv_path, index=False)
        self.df.to_json(json_path, orient="records")
        self.df.to_html(html_path, index=False)
        self.df.to_excel(xlsx_path, index=False)

        manager = ImportManager()
        for path in [csv_path, json_path, html_path, xlsx_path]:
            result = manager.import_file(str(path))
            self.assertTrue(result["success"], str(path))
            self.assertGreaterEqual(len(result["dataframe"]), 1)

        tables = manager.inspect_html_tables(str(html_path))
        self.assertEqual(tables[0]["rows"], 4)

    def test_clean_transform_export_project_roundtrip(self):
        self.dm.load_dataframe(self.df, file_name="ventas.csv")
        cleaner = DataCleaner(self.dm)
        cleaner.remove_duplicates()
        self.assertEqual(len(self.dm.df), 3)

        engine = TransformationEngine(self.dm)
        filtered = engine.filter_rows("amount", ">", 15)
        self.dm.apply_dataframe(filtered, "Filtro amount > 15")
        self.assertEqual(len(self.dm.df), 2)

        out_path = self.root / "export.xlsx"
        result = DataExporter(self.dm).to_excel(str(out_path))
        self.assertTrue(result["success"])
        self.assertTrue(out_path.exists())

        project = self.root / "project"
        ProjectManager.save_project(project, self.dm, {"theme": "dark"})
        fresh = DataManager()
        payload = ProjectManager.load_project(project, fresh)
        self.assertEqual(len(fresh.df), 2)
        self.assertEqual(payload["settings"]["theme"], "dark")

    def test_settings_persist_theme_and_flags(self):
        path = self.root / "settings.json"
        settings = SettingsManager(str(path))
        settings.set("theme", "light")
        settings.set("show_sidebar", False)
        reloaded = SettingsManager(str(path))
        self.assertEqual(reloaded.get("theme"), "light")
        self.assertFalse(reloaded.get("show_sidebar"))


if __name__ == "__main__":
    unittest.main()
