"""Tests for the isolated trial executor input contract."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

from evals.executor import execute_task
from evals.task_loader import load_tasks


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATASET = PROJECT_ROOT / "evals" / "datasets" / "capability" / "b2b_recruiting_meeting_assistant.json"
FIXTURES = PROJECT_ROOT / "evals" / "fixtures"


class ExecutorInputTests(unittest.TestCase):
    def test_written_input_includes_the_expected_project_slug(self) -> None:
        task = next(task for task in load_tasks(DATASET) if task.id == "b2b_recruiting_meeting_assistant")
        with tempfile.TemporaryDirectory() as directory:
            collection_root = Path(directory)
            command = [
                sys.executable,
                "-c",
                "import os, pathlib; pathlib.Path(os.environ['LAUNCH_ENGINE_TRIAL_ROOT'], 'agent-ran.txt').write_text('ok')",
            ]
            result = execute_task(task, collection_root, command, FIXTURES)
            self.assertEqual(result.returncode, 0)
            trial_root = collection_root / task.id
            input_data = json.loads((trial_root / "input.json").read_text(encoding="utf-8"))
            self.assertEqual(input_data["project_slug"], task.expected.project_slug)
            self.assertEqual(input_data["project_slug"], "b2b-recruiting-meeting-assistant")


if __name__ == "__main__":
    unittest.main()
