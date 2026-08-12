import tempfile
import unittest
from pathlib import Path

from app.core.import_manager import ImportManager
from app.core.project_manager import ProjectManager


class ArchitectureUpgradeTest(unittest.TestCase):
    def test_import_manager_exposes_registry_and_default_adapters(self):
        manager = ImportManager()
        self.assertTrue(hasattr(manager, "registry"))
        self.assertGreater(len(manager.registry.list_importers()), 0)
        self.assertIn("csv", manager.registry.supported_formats())

    def test_project_manager_creates_project_structure(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            project = ProjectManager.create_project(Path(tmp_dir) / "demo_project")
            self.assertTrue(project.exists())
            self.assertTrue((project / "datasets").exists())
            self.assertTrue((project / "transformations").exists())
            self.assertTrue((project / "visualizations").exists())


if __name__ == "__main__":
    unittest.main()
