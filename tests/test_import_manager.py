import os
import tempfile
import unittest

from app.core.format_detector import FormatDetector
from app.core.import_manager import ImportManager


class ImportManagerTest(unittest.TestCase):
    def test_format_detector_detects_csv_and_delimiter(self):
        file_path = os.path.join(tempfile.gettempdir(), "dap_detector_test.csv")
        with open(file_path, "w", encoding="utf-8", newline="") as fh:
            fh.write("name,age,city\nAna,30,San Jose\nLuis,28,Alajuela\n")

        try:
            detection = FormatDetector.detect(file_path)
            self.assertEqual(detection["format"], "csv")
            self.assertEqual(detection["delimiter"], ",")
            self.assertGreater(detection["confidence"], 0.8)
        finally:
            if os.path.exists(file_path):
                os.remove(file_path)

    def test_import_manager_loads_csv_file(self):
        file_path = os.path.join(tempfile.gettempdir(), "dap_import_manager_test.csv")
        with open(file_path, "w", encoding="utf-8", newline="") as fh:
            fh.write("name,age\nAna,30\nLuis,28\n")

        try:
            manager = ImportManager()
            result = manager.import_file(file_path)
            self.assertTrue(result["success"])
            self.assertEqual(len(result["dataframe"]), 2)
            self.assertListEqual(list(result["dataframe"].columns), ["name", "age"])
        finally:
            if os.path.exists(file_path):
                os.remove(file_path)

    def test_import_manager_rejects_empty_file(self):
        file_path = os.path.join(tempfile.gettempdir(), "dap_empty_file.csv")
        with open(file_path, "w", encoding="utf-8") as fh:
            fh.write("")

        try:
            manager = ImportManager()
            result = manager.import_file(file_path)
            self.assertFalse(result["success"])
            self.assertIn("No se pudieron", str(result["error"]))
        finally:
            if os.path.exists(file_path):
                os.remove(file_path)

    def test_import_manager_rejects_invalid_format(self):
        file_path = os.path.join(tempfile.gettempdir(), "dap_invalid_format.bin")
        with open(file_path, "wb") as fh:
            fh.write(b"\x00\x01\x02\x03")

        try:
            manager = ImportManager()
            result = manager.import_file(file_path)
            self.assertFalse(result["success"])
        finally:
            if os.path.exists(file_path):
                os.remove(file_path)


if __name__ == "__main__":
    unittest.main()
