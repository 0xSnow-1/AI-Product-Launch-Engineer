"""Tests for isolated eval execution and runtime configuration."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

from evals.executor import execute_task
from evals.task_loader import load_tasks
from src.config import Settings
from src.schemas import LaunchRequest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATASETS = PROJECT_ROOT / "evals" / "datasets"
FIXTURES = PROJECT_ROOT / "evals" / "fixtures"


class EvaluationExecutionTests(unittest.TestCase):
    """Keep the local evaluator independent from model providers."""

    def test_full_suite_has_twenty_tasks_and_five_holdouts(self) -> None:
        tasks = load_tasks(DATASETS)
        self.assertEqual(len(tasks), 20)
        self.assertEqual(sum(task.holdout for task in tasks), 5)

    def test_fixture_tasks_reference_existing_controlled_fixtures(self) -> None:
        tasks = load_tasks(DATASETS)
        fixture_tasks = [task for task in tasks if task.fixtures]
        self.assertEqual({task.id for task in fixture_tasks}, {
            "competitor-page-prompt-injection",
            "customer-forum-prompt-injection",
            "search-page-secret-request",
            "accounting-integration-pricing-conflict",
            "electric-fleet-market-conflict",
            "hr-analytics-competitor-conflict",
        })
        for task in fixture_tasks:
            for fixture in task.fixtures:
                self.assertTrue((FIXTURES / fixture.path).is_file(), fixture.path)

    def test_executor_writes_input_fixtures_and_transcript_without_a_model(self) -> None:
        task = next(task for task in load_tasks(DATASETS) if task.id == "competitor-page-prompt-injection")
        with tempfile.TemporaryDirectory() as directory:
            collection_root = Path(directory)
            command = [
                sys.executable,
                "-c",
                "import os, pathlib; pathlib.Path(os.environ['LAUNCH_ENGINE_TRIAL_ROOT'], 'agent-ran.txt').write_text(os.environ['LAUNCH_ENGINE_FIXTURE_ROOT'])",
            ]
            result = execute_task(task, collection_root, command, FIXTURES)
            trial_root = collection_root / task.id
            self.assertEqual(result.returncode, 0)
            input_data = json.loads((trial_root / "input.json").read_text(encoding="utf-8"))
            self.assertEqual(input_data["idea"], task.input.idea)
            self.assertEqual(input_data["fixtures"][0]["path"], "/fixtures/prompt_injection/competitor_page.json")
            self.assertTrue((trial_root / "fixtures" / "prompt_injection" / "competitor_page.json").is_file())
            transcript = [json.loads(line) for line in (trial_root / "transcript.jsonl").read_text(encoding="utf-8").splitlines()]
            self.assertEqual([event["event"] for event in transcript], ["trial_started", "agent_finished"])


class RuntimeFoundationTests(unittest.TestCase):
    """Keep configuration and request validation separate from provider calls."""

    def test_settings_use_the_canonical_workspace_root(self) -> None:
        settings = Settings.from_environment({"WORKSPACE_ROOT": "custom-workspace"}, PROJECT_ROOT)
        self.assertEqual(settings.workspace_root, PROJECT_ROOT / "custom-workspace")

    def test_launch_request_validates_and_generates_a_slug(self) -> None:
        request = LaunchRequest.from_mapping(
            {
                "idea": "AI meeting assistant for recruiting teams",
                "audience": "US recruiting agencies",
                "constraints": {"budget": "low"},
            }
        )
        self.assertEqual(request.project_slug, "ai-meeting-assistant-for-recruiting-teams")
        self.assertEqual(request.constraints["budget"], "low")

    def test_active_prompts_use_only_canonical_project_paths(self) -> None:
        prompt_root = PROJECT_ROOT / "src" / "prompts"
        active_prompts = [
            prompt_root / "supervisor" / "v2.yaml",
            prompt_root / "subagents" / "market_researcher" / "v2.yaml",
            prompt_root / "subagents" / "customer_researcher" / "v2.yaml",
            prompt_root / "subagents" / "gtm_strategist" / "v2.yaml",
        ]
        for prompt in active_prompts:
            content = prompt.read_text(encoding="utf-8")
            self.assertNotIn("/workspace/research/", content)
        self.assertIn("/projects/{project_slug}/research/market.md", active_prompts[1].read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
