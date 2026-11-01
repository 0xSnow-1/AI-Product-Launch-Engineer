"""Behavior tests for the task loader, graders, and command-line runner."""

from __future__ import annotations

import io
import json
import tempfile
import unittest
import zipfile
from contextlib import redirect_stdout
from pathlib import Path

from evals.evaluators import grade_trial
from evals.run_evals import main
from evals.task_loader import load_tasks


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SEED_DATASET = PROJECT_ROOT / "evals" / "datasets" / "capability" / "b2b_recruiting_meeting_assistant.json"


def _write_complete_trial(task, trial_root: Path) -> None:
    project_root = trial_root / "projects" / task.expected.project_slug
    contents: dict[str, str] = {}
    for virtual_path, headings in task.expected.required_sections.items():
        relative_path = virtual_path.removeprefix(f"/projects/{task.expected.project_slug}/")
        contents[relative_path] = "\n".join(f"# {heading}" for heading in headings) + "\n"
    contents["research/market.md"] += (
        "\n- [Bureau of Labor Statistics](https://www.bls.gov/oes/current/oes131072.htm)\n"
        "- [U.S. Census Bureau](https://www.census.gov/programs-surveys.html)\n"
        "- [Federal Trade Commission](https://www.ftc.gov/business-guidance)\n"
    )
    for relative_path, content in contents.items():
        target = project_root / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")

    manifest = {
        "metadata": {
            "project_slug": task.expected.project_slug,
            "created_at": "2026-11-01T00:00:00Z",
            "version": "1.0.0",
        },
        "artifacts": ["market.md", "customers.md", "gtm.md", "blueprint.md", "manifest.json"],
        "execution": {
            "agents_used": list(task.expected.manifest_agents),
            "total_turns": 4,
            "total_tool_calls": 12,
            "total_tokens": 3200,
        },
    }
    (project_root / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    with zipfile.ZipFile(project_root / "deliverable.zip", "w") as archive:
        for virtual_path in task.expected.artifacts:
            if virtual_path.endswith(".zip"):
                continue
            relative_path = virtual_path.removeprefix(f"/projects/{task.expected.project_slug}/")
            archive.write(project_root / relative_path, arcname=relative_path)


class EvaluationHarnessTests(unittest.TestCase):
    def setUp(self) -> None:
        self.task = load_tasks(SEED_DATASET)[0]

    def test_loader_reads_one_valid_seed_task(self) -> None:
        tasks = load_tasks(SEED_DATASET.parent)
        self.assertEqual([task.id for task in tasks], ["b2b_recruiting_meeting_assistant"])

    def test_complete_trial_passes_all_deterministic_graders(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            trial_root = Path(temporary_directory)
            _write_complete_trial(self.task, trial_root)
            report = grade_trial(self.task, trial_root)
        self.assertTrue(report.passed, report.to_dict())

    def test_missing_artifact_fails_the_trial(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            trial_root = Path(temporary_directory)
            _write_complete_trial(self.task, trial_root)
            market_path = trial_root / "projects" / self.task.expected.project_slug / "research" / "market.md"
            market_path.unlink()
            report = grade_trial(self.task, trial_root)
        artifact_result = next(result for result in report.results if result.grader_name == "artifact_exists")
        self.assertFalse(report.passed)
        self.assertFalse(artifact_result.passed)
        self.assertIn("/projects/b2b-recruiting-meeting-assistant/research/market.md", artifact_result.details["missing_artifacts"])

    def test_invalid_source_url_fails_even_when_the_source_minimum_is_met(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            trial_root = Path(temporary_directory)
            _write_complete_trial(self.task, trial_root)
            market_path = trial_root / "projects" / self.task.expected.project_slug / "research" / "market.md"
            market_path.write_text(f"{market_path.read_text(encoding='utf-8')}\n- [Invalid](ftp://example.com)\n", encoding="utf-8")
            report = grade_trial(self.task, trial_root)
        citation_result = next(result for result in report.results if result.grader_name == "source_citations")
        self.assertFalse(citation_result.passed)
        self.assertEqual(citation_result.details["invalid_urls"], ["ftp://example.com"])

    def test_placeholder_fails_the_trial(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            trial_root = Path(temporary_directory)
            _write_complete_trial(self.task, trial_root)
            customer_path = trial_root / "projects" / self.task.expected.project_slug / "research" / "customers.md"
            customer_path.write_text(f"{customer_path.read_text(encoding='utf-8')}\n[citation needed]\n", encoding="utf-8")
            report = grade_trial(self.task, trial_root)
        placeholder_result = next(result for result in report.results if result.grader_name == "placeholders")
        self.assertFalse(placeholder_result.passed)
        self.assertIn("[citation needed]", placeholder_result.details["placeholders"]["/projects/b2b-recruiting-meeting-assistant/research/customers.md"])

    def test_runner_validates_the_dataset_without_trial_artifacts(self) -> None:
        output = io.StringIO()
        with redirect_stdout(output):
            exit_code = main(["--datasets", str(SEED_DATASET.parent), "--validate-only"])
        report = json.loads(output.getvalue())
        self.assertEqual(exit_code, 0)
        self.assertTrue(report["valid"])
        self.assertEqual(report["task_ids"], ["b2b_recruiting_meeting_assistant"])

    def test_runner_grades_a_complete_isolated_trial(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            trial_collection = Path(temporary_directory)
            _write_complete_trial(self.task, trial_collection / self.task.id)
            output = io.StringIO()
            with redirect_stdout(output):
                exit_code = main(
                    [
                        "--datasets",
                        str(SEED_DATASET.parent),
                        "--trial-root",
                        str(trial_collection),
                    ]
                )
        report = json.loads(output.getvalue())
        self.assertEqual(exit_code, 0)
        self.assertTrue(report["passed"])


if __name__ == "__main__":
    unittest.main()
