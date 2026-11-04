"""Tests for the self-contained HTML results report."""

from __future__ import annotations

import io
import json
import shutil
import tempfile
import unittest
import zipfile
from contextlib import redirect_stdout
from pathlib import Path
from typing import Any

from evals.evaluators import EvaluationReport, grade_trial
from evals.report_html import main
from evals.run_evals import main as run_evals_main
from evals.task_loader import load_tasks


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATASET = PROJECT_ROOT / "evals" / "datasets" / "capability" / "b2b_recruiting_meeting_assistant.json"
REFERENCE_ROOT = PROJECT_ROOT / "evals" / "reference" / "b2b_recruiting_meeting_assistant"
FIXTURES = PROJECT_ROOT / "evals" / "fixtures" / "transcripts"
ARCHIVE_FILES = (
    "research/market_research.json",
    "research/customer_research.json",
    "strategy/gtm_strategy.json",
    "blueprint.md",
    "manifest.json",
)


def _write_input(trial_root: Path, task: Any) -> None:
    (trial_root / "input.json").write_text(
        json.dumps(
            {
                "idea": task.input.idea,
                "audience": task.input.audience,
                "constraints": dict(task.input.constraints),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def _build_trial(
    task: Any,
    trial_root: Path,
    transcript_fixture: str,
    *,
    missing_market: bool = False,
    extra_markdown: str | None = None,
) -> EvaluationReport:
    shutil.copytree(REFERENCE_ROOT, trial_root, dirs_exist_ok=True)
    project_root = trial_root / "projects" / task.expected.project_slug
    if extra_markdown:
        blueprint = project_root / "blueprint.md"
        blueprint.write_text(
            f"{blueprint.read_text(encoding='utf-8')}\n{extra_markdown}\n",
            encoding="utf-8",
        )
    with zipfile.ZipFile(project_root / "deliverable.zip", "w") as archive:
        for name in ARCHIVE_FILES:
            archive.write(project_root / name, arcname=name)
    if missing_market:
        (project_root / "research" / "market_research.json").unlink()
    _write_input(trial_root, task)
    shutil.copyfile(FIXTURES / transcript_fixture, trial_root / "transcript.jsonl")
    report = grade_trial(task, trial_root)
    (trial_root / "grader_results.json").write_text(
        json.dumps(report.to_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report


def _write_summary(
    run_dir: Path,
    reports: list[dict[str, Any]],
    *,
    passed: bool,
) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "run_id": run_dir.name,
        "created_at": "2026-11-02T00:00:00Z",
        "commit": "abc123",
        "model_id": "test-model",
        "passed": passed,
        "reports": reports,
        "executions": [],
    }
    (run_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")


def _render(run_dir: Path) -> tuple[Path, str]:
    output = io.StringIO()
    with redirect_stdout(output):
        exit_code = main(["--run", str(run_dir)])
    if exit_code != 0:
        raise AssertionError(f"report command failed: {output.getvalue()}")
    report_path = run_dir / "report.html"
    return report_path, report_path.read_text(encoding="utf-8")


class ReportHtmlTests(unittest.TestCase):
    def setUp(self) -> None:
        self.task = load_tasks(DATASET)[0]

    def _single_run(self, directory: Path, *, failing: bool = False) -> Path:
        run_dir = directory / "run"
        trial_root = run_dir / "trials" / self.task.id
        trial_root.mkdir(parents=True)
        report = _build_trial(
            self.task,
            trial_root,
            "gtm_before_customer_result.jsonl" if failing else "pass_parallel.jsonl",
            missing_market=failing,
        )
        _write_summary(run_dir, [report.to_dict()], passed=not failing)
        return run_dir

    def test_passing_run_shows_status_cards_table_and_gtm_badge(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            run_dir = self._single_run(Path(directory))
            report_path, text = _render(run_dir)
            self.assertTrue(report_path.is_file())
            self.assertIn('class="kpi-cards"', text)
            self.assertIn('class="task-table"', text)
            self.assertIn("Pass rate", text)
            self.assertIn("Failed tasks", text)
            self.assertIn("Total tool calls", text)
            self.assertIn("GTM after both research", text)
            self.assertIn("badge-pass", text)
            self.assertIn("b2b_recruiting_meeting_assistant", text)

    def test_failing_run_shows_fail_status_and_failure_class(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            run_dir = self._single_run(Path(directory), failing=True)
            _, text = _render(run_dir)
            self.assertIn("badge-fail", text)
            self.assertIn("FAIL", text)
            self.assertIn("Missing artifact", text)
            self.assertIn("Bad delegation", text)
            self.assertIn("GTM after both research", text)

    def test_raw_html_in_artifact_is_escaped(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            run_dir = Path(directory) / "run"
            trial_root = run_dir / "trials" / self.task.id
            trial_root.mkdir(parents=True)
            payload = '<script>alert("xss")</script>'
            report = _build_trial(
                self.task,
                trial_root,
                "pass_parallel.jsonl",
                extra_markdown=payload,
            )
            _write_summary(run_dir, [report.to_dict()], passed=True)
            _, text = _render(run_dir)
            self.assertNotIn(payload, text)
            self.assertIn("&lt;script&gt;alert", text)

    def test_report_has_no_external_assets(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            run_dir = self._single_run(Path(directory))
            _, text = _render(run_dir)
            self.assertNotIn("<script src=", text)
            self.assertNotIn('<link href="http', text)
            self.assertNotIn("@import url(http", text)

    def test_output_flag_writes_to_a_custom_path(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            run_dir = self._single_run(root)
            custom = root / "nested" / "custom.html"
            output = io.StringIO()
            with redirect_stdout(output):
                exit_code = main(["--run", str(run_dir), "--output", str(custom)])
            self.assertEqual(exit_code, 0)
            self.assertTrue(custom.is_file())
            self.assertIn(str(custom), output.getvalue())

    def test_multi_task_run_renders_every_task(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            run_dir = Path(directory) / "run"
            reports: list[dict[str, Any]] = []
            for label, failing in (("task-a", False), ("task-b", True)):
                trial_root = run_dir / "trials" / label
                trial_root.mkdir(parents=True)
                report = _build_trial(
                    self.task,
                    trial_root,
                    "gtm_before_customer_result.jsonl" if failing else "pass_parallel.jsonl",
                    missing_market=failing,
                )
                payload = report.to_dict()
                payload["task_id"] = label
                reports.append(payload)
            _write_summary(run_dir, reports, passed=False)
            _, text = _render(run_dir)
            self.assertIn("task-a", text)
            self.assertIn("task-b", text)
            self.assertEqual(text.count('class="task-detail"'), 2)

    def test_missing_summary_renders_an_empty_state(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            run_dir = Path(directory) / "empty-run"
            run_dir.mkdir()
            report_path, text = _render(run_dir)
            self.assertTrue(report_path.is_file())
            self.assertIn("No task results found", text)
            self.assertIn("UNKNOWN", text)

    def test_runner_html_flag_writes_report_and_keeps_json(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            run_dir = root / "run"
            trial_root = run_dir / "trials" / self.task.id
            trial_root.mkdir(parents=True)
            _build_trial(self.task, trial_root, "pass_parallel.jsonl")
            output = io.StringIO()
            with redirect_stdout(output):
                exit_code = run_evals_main(
                    [
                        "--datasets",
                        str(DATASET),
                        "--task",
                        self.task.id,
                        "--runs-root",
                        str(root),
                        "--run-id",
                        "run",
                        "--html",
                    ]
                )
            self.assertEqual(exit_code, 0)
            self.assertTrue((run_dir / "summary.json").is_file())
            self.assertTrue((run_dir / "report.html").is_file())
            self.assertIn("Report written to", output.getvalue())
            self.assertIn("badge-pass", (run_dir / "report.html").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
