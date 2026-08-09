import importlib.util
import sys
import unittest
from pathlib import Path


class ProjectRunnerTest(unittest.TestCase):
    def test_project_main_module_can_be_imported(self):
        project_dir = Path(__file__).resolve().parents[1] / "PROYECTO 2 UCR"
        main_path = project_dir / "main.py"

        self.assertTrue(main_path.exists(), "No se encontró el archivo main.py del proyecto")

        spec = importlib.util.spec_from_file_location("project_main", main_path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        assert spec.loader is not None
        spec.loader.exec_module(module)

        self.assertTrue(hasattr(module, "main"))


if __name__ == "__main__":
    unittest.main()
