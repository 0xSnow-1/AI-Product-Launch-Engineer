"""Tests for launch deliverable packaging."""

from __future__ import annotations

import io
import json
import shutil
import tempfile
import unittest
import zipfile
from pathlib import Path

from agents.supervisor import create_blueprint
from evals.evaluators import ArchiveGrader, ManifestGrader
from evals.task_loader import load_tasks
from src.metrics import collect_metrics
from workflows.packaging import build_deliverable, write_manifest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATASET = PROJECT_ROOT / "evals" / "datasets" / "capability" / "b2b_recruiting_meeting_assistant.json"
REFERENCE_ROOT = PROJECT_ROOT / "evals" / "reference" / "b2b_recruiting_meeting_assistant"
EXPECTED_ARCHIVE_ENTRIES = frozenset(
    {
        "research/market_research.json",
        "research/customer_research.json",
        "strategy/gtm_strategy.json",
        "blueprint.md",
        "manifest.json",
    }
)
EXPECTED_MANIFEST_ARTIFACTS = ("market_research.json", "customer_research.json", "gtm_strategy.json", "blueprint.md", "manifest.json")
EXPECTED_MANIFEST_AGENTS = ("market_researcher", "customer_researcher", "gtm_strategist", "supervisor")


class PackagingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.task = load_tasks(DATASET)[0]

    def test_packaging_writes_a_contract_manifest_and_deliverable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            trial_root = Path(directory)
            project_root = trial_root / "projects" / self.task.expected.project_slug
            shutil.copytree(REFERENCE_ROOT, trial_root, dirs_exist_ok=True)

            write_manifest(
                project_root,
                self.task.expected.project_slug,
                list(self.task.expected.manifest_agents),
                {"total_turns": 4, "total_tool_calls": 12, "total_tokens": 3200},
            )
            archive_path = build_deliverable(project_root, self.task.expected.project_slug)

            self.assertTrue(archive_path.is_file())
            with zipfile.ZipFile(archive_path) as archive:
                self.assertEqual(set(archive.namelist()), set(EXPECTED_ARCHIVE_ENTRIES))

            manifest = json.loads((project_root / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["metadata"]["project_slug"], self.task.expected.project_slug)
            self.assertEqual(list(manifest["artifacts"]), list(EXPECTED_MANIFEST_ARTIFACTS))
            execution = manifest["execution"]
            self.assertEqual(set(execution["agents_used"]), set(EXPECTED_MANIFEST_AGENTS))
            for metric in ("total_turns", "total_tool_calls", "total_tokens"):
                self.assertIsInstance(execution[metric], int)
                self.assertGreaterEqual(execution[metric], 0)

            manifest_result = ManifestGrader().grade(self.task, trial_root)
            self.assertTrue(manifest_result.passed, manifest_result.details)
            archive_result = ArchiveGrader().grade(self.task, trial_root)
            self.assertTrue(archive_result.passed, archive_result.details)

    def test_simulated_run_produces_all_six_contract_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            trial_root = Path(directory)
            project_root = trial_root / "projects" / self.task.expected.project_slug
            shutil.copytree(REFERENCE_ROOT, trial_root, dirs_exist_ok=True)

            create_blueprint(object(), self.task.expected.project_slug, trial_root, io.StringIO())
            write_manifest(
                project_root,
                self.task.expected.project_slug,
                list(self.task.expected.manifest_agents),
                {"total_turns": 4, "total_tool_calls": 12, "total_tokens": 3200},
            )
            build_deliverable(project_root, self.task.expected.project_slug)

            expected_artifacts = (
                "research/market_research.json",
                "research/customer_research.json",
                "strategy/gtm_strategy.json",
                "blueprint.md",
                "manifest.json",
                "deliverable.zip",
            )
            for relative_path in expected_artifacts:
                self.assertTrue((project_root / relative_path).is_file(), relative_path)

    def test_metrics_return_zero_when_transcript_is_absent(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            metrics = collect_metrics(Path(directory) / "missing-transcript.jsonl")
        self.assertEqual(metrics["total_turns"], 0)
        self.assertEqual(metrics["total_tool_calls"], 0)
        self.assertEqual(metrics["total_tokens"], 0)
        self.assertEqual(list(metrics.get("agents_used") or []), [])


if __name__ == "__main__":
    unittest.main()
