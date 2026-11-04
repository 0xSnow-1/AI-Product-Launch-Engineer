"""Tests for transcript usage capture and metrics aggregation."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from src.metrics import collect_metrics
from src.transcript import _usage_from_response


def _write_transcript(path: Path, events: list[dict]) -> None:
    path.write_text("".join(f"{json.dumps(event)}\n" for event in events), encoding="utf-8")


class AgentsUsedTests(unittest.TestCase):
    def test_supervisor_is_always_listed_when_transcript_exists(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "transcript.jsonl"
            _write_transcript(path, [{"event": "model_started", "timestamp": "2026-11-04T00:00:00Z"}])
            metrics = collect_metrics(path)
        self.assertEqual(metrics["agents_used"][0], "supervisor")

    def test_subagents_follow_the_supervisor(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "transcript.jsonl"
            _write_transcript(
                path,
                [
                    {"event": "model_started", "timestamp": "2026-11-04T00:00:00Z"},
                    {
                        "event": "tool_started",
                        "tool": "task",
                        "input": json.dumps({"subagent_type": "market_researcher"}),
                        "timestamp": "2026-11-04T00:00:01Z",
                    },
                ],
            )
            metrics = collect_metrics(path)
        self.assertEqual(metrics["agents_used"], ["supervisor", "market_researcher"])

    def test_missing_transcript_lists_no_agents(self) -> None:
        metrics = collect_metrics(Path("/tmp/does-not-exist-metrics-test.jsonl"))
        self.assertEqual(metrics["agents_used"], [])


class UsageCaptureTests(unittest.TestCase):
    def test_usage_reads_message_usage_metadata(self) -> None:
        message = SimpleNamespace(
            usage_metadata={"input_tokens": 120, "output_tokens": 30, "total_tokens": 150},
            response_metadata={},
        )
        response = SimpleNamespace(
            generations=[[SimpleNamespace(message=message)]],
            llm_output={},
        )
        self.assertEqual(
            _usage_from_response(response),
            {"input_tokens": 120, "output_tokens": 30, "total_tokens": 150},
        )

    def test_usage_falls_back_to_llm_output(self) -> None:
        response = SimpleNamespace(
            generations=[],
            llm_output={"usage": {"input_tokens": 10, "output_tokens": 5, "total_tokens": 15}},
        )
        self.assertEqual(
            _usage_from_response(response),
            {"input_tokens": 10, "output_tokens": 5, "total_tokens": 15},
        )

    def test_usage_computes_total_from_parts(self) -> None:
        response = SimpleNamespace(
            generations=[],
            llm_output={"input_tokens": 8, "output_tokens": 4},
        )
        self.assertEqual(
            _usage_from_response(response),
            {"input_tokens": 8, "output_tokens": 4, "total_tokens": 12},
        )

    def test_usage_is_absent_when_no_metadata_exists(self) -> None:
        response = SimpleNamespace(generations=[], llm_output={})
        self.assertIsNone(_usage_from_response(response))

    def test_total_tokens_sums_across_model_events(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "transcript.jsonl"
            _write_transcript(
                path,
                [
                    {"event": "model_started", "timestamp": "2026-11-04T00:00:00Z"},
                    {
                        "event": "model_finished",
                        "timestamp": "2026-11-04T00:00:01Z",
                        "usage": {"input_tokens": 100, "output_tokens": 20, "total_tokens": 120},
                    },
                    {
                        "event": "model_finished",
                        "timestamp": "2026-11-04T00:00:02Z",
                        "usage": {"input_tokens": 50, "output_tokens": 10},
                    },
                ],
            )
            metrics = collect_metrics(path)
        self.assertEqual(metrics["total_tokens"], 180)


if __name__ == "__main__":
    unittest.main()
