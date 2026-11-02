"""Tests for the delegation grader and the transcript callback handler."""

from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path
from typing import Any

from evals.evaluators import DelegationGrader, GradingResult
from evals.task_loader import load_tasks
from src.transcript import JsonlCallbackHandler


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATASET = PROJECT_ROOT / "evals" / "datasets" / "capability" / "b2b_recruiting_meeting_assistant.json"
FIXTURES = PROJECT_ROOT / "evals" / "fixtures" / "transcripts"


class DelegationGraderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.task = load_tasks(DATASET)[0]
        self.grader = DelegationGrader()

    def _grade(self, fixture_name: str) -> GradingResult:
        with tempfile.TemporaryDirectory() as directory:
            trial_root = Path(directory)
            shutil.copyfile(FIXTURES / fixture_name, trial_root / "transcript.jsonl")
            return self.grader.grade(self.task, trial_root)

    def test_task_defaults_include_three_subagents_and_sixty_tool_calls(self) -> None:
        self.assertEqual(
            self.task.expected.required_subagents,
            ("market_researcher", "customer_researcher", "gtm_strategist"),
        )
        self.assertEqual(self.task.expected.max_tool_calls, 60)

    def test_parallel_research_passes(self) -> None:
        result = self._grade("pass_parallel.jsonl")
        self.assertTrue(result.passed, result.details)
        self.assertEqual(
            set(result.details["delegated_subagents"]),
            set(self.task.expected.required_subagents),
        )
        self.assertEqual(result.details["missing_subagents"], [])
        self.assertTrue(result.details["gtm_after_both_research"])
        self.assertLessEqual(result.details["tool_call_count"], result.details["max_tool_calls"])
        self.assertTrue(result.details["research_artifact_writes"])

    def test_sequential_explicit_delegation_passes(self) -> None:
        result = self._grade("pass_sequential.jsonl")
        self.assertTrue(result.passed, result.details)
        self.assertTrue(result.details["gtm_after_both_research"])

    def test_gtm_before_customer_result_fails(self) -> None:
        result = self._grade("gtm_before_customer_result.jsonl")
        self.assertFalse(result.passed)
        self.assertFalse(result.details["gtm_after_both_research"])
        self.assertIn("customer_researcher", " ".join(result.details["errors"]))

    def test_gtm_before_both_results_fails(self) -> None:
        result = self._grade("gtm_before_both_results.jsonl")
        self.assertFalse(result.passed)
        self.assertFalse(result.details["gtm_after_both_research"])

    def test_missing_customer_result_fails(self) -> None:
        result = self._grade("missing_customer_result.jsonl")
        self.assertFalse(result.passed)
        self.assertIn("missing finish for customer_researcher", " ".join(result.details["errors"]))
        self.assertFalse(result.details["gtm_after_both_research"])

    def test_missing_run_id_fails_the_dependency_gate(self) -> None:
        result = self._grade("missing_run_id.jsonl")
        self.assertFalse(result.passed)
        errors = " ".join(result.details["errors"])
        self.assertIn("missing run_id", errors)
        self.assertIn("cannot be proven", errors)
        self.assertTrue(result.details["missing_run_id_lines"])

    def test_tool_loop_fails_the_budget(self) -> None:
        result = self._grade("tool_loop.jsonl")
        self.assertFalse(result.passed)
        self.assertGreater(result.details["tool_call_count"], result.details["max_tool_calls"])
        self.assertIn("exceeds budget", " ".join(result.details["errors"]))

    def test_malformed_transcript_returns_a_failed_result(self) -> None:
        result = self._grade("malformed.jsonl")
        self.assertFalse(result.passed)
        self.assertEqual(result.details["malformed_lines"][0]["line"], 2)
        self.assertIn("malformed", result.details["error"])

    def test_missing_transcript_returns_a_failed_result(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result = self.grader.grade(self.task, Path(directory))
        self.assertFalse(result.passed)
        self.assertEqual(result.details["error"], "transcript.jsonl is missing")


class TranscriptHandlerTests(unittest.TestCase):
    def _events(self, path: Path) -> list[dict[str, Any]]:
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]

    def test_tool_end_reuses_the_cached_tool_name_and_records_context(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "transcript.jsonl"
            handler = JsonlCallbackHandler(path)
            handler.on_tool_start(
                {"name": "task"},
                "{'subagent_type': 'market_researcher'}",
                run_id="run-1",
                parent_run_id="parent-1",
                tags=["eval"],
                metadata={"step": 1},
            )
            handler.on_tool_end("done", run_id="run-1", parent_run_id="parent-1")
            start, finish = self._events(path)
        self.assertEqual(start["run_id"], "run-1")
        self.assertEqual(start["parent_run_id"], "parent-1")
        self.assertEqual(start["tags"], ["eval"])
        self.assertEqual(start["metadata"], {"step": 1})
        self.assertEqual(start["tool"], "task")
        self.assertEqual(finish["tool"], "task")
        self.assertEqual(finish["run_id"], "run-1")

    def test_model_events_include_the_model_name(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "transcript.jsonl"
            handler = JsonlCallbackHandler(path)
            handler.on_chat_model_start({"name": "test-model"}, [], run_id="model-1")
            handler.on_llm_end("ok", run_id="model-1")
            started, finished = self._events(path)
        self.assertEqual(started["model"], "test-model")
        self.assertEqual(finished["model"], "test-model")
        self.assertEqual(started["run_id"], "model-1")


if __name__ == "__main__":
    unittest.main()
