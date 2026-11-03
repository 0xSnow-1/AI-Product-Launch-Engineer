"""Tests for blueprint assembly under the isolated workspace root."""

from __future__ import annotations

import io
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from agents.supervisor import create_blueprint  # noqa: E402


PROJECT_SLUG = "b2b-recruiting-meeting-assistant"


class BlueprintLocationTests(unittest.TestCase):
    def _seed_research(self, project_root: Path) -> None:
        (project_root / "research").mkdir(parents=True, exist_ok=True)
        (project_root / "research" / "market.md").write_text("# Market Research\n", encoding="utf-8")
        (project_root / "research" / "customers.md").write_text("# Customer Research\n", encoding="utf-8")
        (project_root / "strategy").mkdir(parents=True, exist_ok=True)
        (project_root / "strategy" / "gtm.md").write_text("# GTM Strategy\n", encoding="utf-8")

    def test_blueprint_writes_under_the_workspace_root(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace_root = Path(directory)
            project_root = workspace_root / "projects" / PROJECT_SLUG
            self._seed_research(project_root)
            output = io.StringIO()
            create_blueprint(object(), PROJECT_SLUG, workspace_root, output)
            blueprint_path = project_root / "blueprint.md"
            self.assertTrue(blueprint_path.is_file())
            self.assertIn(PROJECT_SLUG, blueprint_path.read_text(encoding="utf-8"))

    def test_blueprint_does_not_write_under_host_projects(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace_root = Path(directory)
            project_root = workspace_root / "projects" / PROJECT_SLUG
            self._seed_research(project_root)
            create_blueprint(object(), PROJECT_SLUG, workspace_root, io.StringIO())
            self.assertFalse((Path("/projects") / PROJECT_SLUG / "blueprint.md").exists())


if __name__ == "__main__":
    unittest.main()
