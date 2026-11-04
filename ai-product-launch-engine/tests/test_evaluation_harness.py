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


def _market_research(project_slug: str) -> dict:
    now = "2026-11-01T00:00:00Z"
    evidence = [
        ("Bureau of Labor Statistics", "https://www.bls.gov/oes/current/oes131072.htm"),
        ("U.S. Census Bureau", "https://www.census.gov/programs-surveys.html"),
        ("Federal Trade Commission", "https://www.ftc.gov/business-guidance"),
    ]
    return {
        "project_id": project_slug,
        "generated_at": now,
        "summary": "Narrow recruiting niche with a clear gap.",
        "competitors": [
            {"name": "Example ATS", "positioning": "Applicant tracking with add-ons"}
        ],
        "market_opportunities": ["Small agencies lack structured intake notes"],
        "trends": ["Remote intake calls are common"],
        "claims": [
            {
                "id": f"market-{index}",
                "text": f"Sourced claim {index}.",
                "kind": "fact",
                "evidence_refs": [
                    {
                        "title": title,
                        "url": url,
                        "retrieved_at": now,
                        "claim_ids": [f"market-{index}"],
                    }
                ],
            }
            for index, (title, url) in enumerate(evidence, 1)
        ],
        "assumptions": ["Agencies will pilot within 90 days"],
        "limitations": ["No primary survey was run"],
    }


def _customer_research(project_slug: str) -> dict:
    return {
        "project_id": project_slug,
        "generated_at": "2026-11-01T00:00:00Z",
        "segments": [{"name": "Small agencies", "description": "5 to 50 recruiters"}],
        "personas": [{"name": "Agency owner", "role": "buyer"}],
        "pain_points": ["Notes are retyped into the ATS"],
        "buying_triggers": ["New client volume exceeds capacity"],
        "ideal_customer_profile": "US recruiting agency with 5 to 50 recruiters",
        "claims": [],
        "assumptions": ["Owners approve pilots"],
        "limitations": ["Interview data is hypothetical"],
    }


def _gtm_strategy(project_slug: str) -> dict:
    return {
        "project_id": project_slug,
        "generated_at": "2026-11-01T00:00:00Z",
        "positioning": "The intake-call assistant for small recruiting agencies",
        "differentiation": "Structured notes and ATS follow-up actions",
        "target_segments": ["Small US recruiting agencies"],
        "pricing_hypotheses": ["Low monthly fee per recruiter"],
        "channels": ["Direct outreach", "ATS marketplaces"],
        "launch_roadmap": [
            {"name": "Pilot", "timeline": "Weeks 1 to 6", "activities": ["Recruit ten agencies"]}
        ],
        "risks": ["ATS integration access delays the pilot"],
        "assumptions": ["Agencies accept a paid pilot"],
        "claims": [],
    }


def _write_complete_trial(task, trial_root: Path) -> None:
    project_root = trial_root / "projects" / task.expected.project_slug
    contents: dict[str, str] = {}
    for virtual_path, headings in task.expected.required_sections.items():
        relative_path = virtual_path.removeprefix(f"/projects/{task.expected.project_slug}/")
        contents[relative_path] = "\n".join(f"# {heading}" for heading in headings) + "\n"
    json_artifacts = {
        "research/market_research.json": _market_research(task.expected.project_slug),
        "research/customer_research.json": _customer_research(task.expected.project_slug),
        "strategy/gtm_strategy.json": _gtm_strategy(task.expected.project_slug),
    }
    for relative_path, payload in json_artifacts.items():
        target = project_root / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(payload, indent=2), encoding="utf-8")
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
        "artifacts": ["market_research.json", "customer_research.json", "gtm_strategy.json", "blueprint.md", "manifest.json"],
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

    transcript = [
        {
            "event": "tool_started",
            "run_id": "market-1",
            "tool": "task",
            "input": json.dumps({"subagent_type": "market_researcher"}),
            "timestamp": "2026-11-01T00:00:00Z",
        },
        {
            "event": "tool_started",
            "run_id": "customer-1",
            "tool": "task",
            "input": json.dumps({"subagent_type": "customer_researcher"}),
            "timestamp": "2026-11-01T00:00:01Z",
        },
        {
            "event": "tool_finished",
            "run_id": "market-1",
            "tool": "task",
            "output": "market research complete",
            "timestamp": "2026-11-01T00:00:05Z",
        },
        {
            "event": "tool_finished",
            "run_id": "customer-1",
            "tool": "task",
            "output": "customer research complete",
            "timestamp": "2026-11-01T00:00:06Z",
        },
        {
            "event": "tool_started",
            "run_id": "gtm-1",
            "tool": "task",
            "input": json.dumps({"subagent_type": "gtm_strategist"}),
            "timestamp": "2026-11-01T00:00:10Z",
        },
        {
            "event": "tool_finished",
            "run_id": "gtm-1",
            "tool": "task",
            "output": "gtm strategy complete",
            "timestamp": "2026-11-01T00:00:20Z",
        },
    ]
    (trial_root / "transcript.jsonl").write_text(
        "".join(f"{json.dumps(event)}\n" for event in transcript),
        encoding="utf-8",
    )


class EvaluationHarnessTests(unittest.TestCase):
    def setUp(self) -> None:
        self.task = load_tasks(SEED_DATASET)[0]

    def test_loader_reads_one_valid_seed_task(self) -> None:
        tasks = load_tasks(SEED_DATASET)
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
            market_path = trial_root / "projects" / self.task.expected.project_slug / "research" / "market_research.json"
            market_path.unlink()
            report = grade_trial(self.task, trial_root)
        artifact_result = next(result for result in report.results if result.grader_name == "artifact_exists")
        self.assertFalse(report.passed)
        self.assertFalse(artifact_result.passed)
        self.assertIn("/projects/b2b-recruiting-meeting-assistant/research/market_research.json", artifact_result.details["missing_artifacts"])

    def test_invalid_source_url_fails_even_when_the_source_minimum_is_met(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            trial_root = Path(temporary_directory)
            _write_complete_trial(self.task, trial_root)
            market_path = trial_root / "projects" / self.task.expected.project_slug / "research" / "market_research.json"
            market = json.loads(market_path.read_text(encoding="utf-8"))
            market["claims"][0]["evidence_refs"][0]["url"] = "ftp://example.com"
            market_path.write_text(json.dumps(market), encoding="utf-8")
            report = grade_trial(self.task, trial_root)
        citation_result = next(result for result in report.results if result.grader_name == "source_citations")
        self.assertFalse(citation_result.passed)
        self.assertEqual(citation_result.details["invalid_urls"], ["ftp://example.com"])

    def test_placeholder_fails_the_trial(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            trial_root = Path(temporary_directory)
            _write_complete_trial(self.task, trial_root)
            customer_path = trial_root / "projects" / self.task.expected.project_slug / "research" / "customer_research.json"
            customer = json.loads(customer_path.read_text(encoding="utf-8"))
            customer["limitations"] = ["[citation needed]"]
            customer_path.write_text(json.dumps(customer), encoding="utf-8")
            report = grade_trial(self.task, trial_root)
        placeholder_result = next(result for result in report.results if result.grader_name == "placeholders")
        self.assertFalse(placeholder_result.passed)
        self.assertIn("[citation needed]", placeholder_result.details["placeholders"]["/projects/b2b-recruiting-meeting-assistant/research/customer_research.json"])

    def test_runner_validates_the_dataset_without_trial_artifacts(self) -> None:
        output = io.StringIO()
        with redirect_stdout(output):
            exit_code = main(["--datasets", str(SEED_DATASET), "--validate-only"])
        report = json.loads(output.getvalue())
        self.assertEqual(exit_code, 0)
        self.assertTrue(report["valid"])
        self.assertEqual(report["task_ids"], ["b2b_recruiting_meeting_assistant"])

    def test_runner_grades_a_complete_isolated_trial(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            run_dir = root / "run"
            trial_root = run_dir / "trials" / self.task.id
            _write_complete_trial(self.task, trial_root)
            output = io.StringIO()
            with redirect_stdout(output):
                exit_code = main(
                    [
                        "--datasets",
                        str(SEED_DATASET),
                        "--runs-root",
                        str(root),
                        "--run-id",
                        "run",
                    ]
                )
            self.assertTrue((trial_root / "grader_results.json").is_file())
            self.assertTrue((run_dir / "summary.json").is_file())
            report = json.loads((run_dir / "summary.json").read_text(encoding="utf-8"))
        self.assertEqual(exit_code, 0)
        self.assertTrue(report["passed"])
        self.assertIn("Run directory:", output.getvalue())


if __name__ == "__main__":
    unittest.main()
