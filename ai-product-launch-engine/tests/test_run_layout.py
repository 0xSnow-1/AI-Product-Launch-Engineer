"""Behavior tests for the eval run layout and run id generation."""

from __future__ import annotations

import io
import re
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from evals.run_evals import _default_run_id, main
from evals.task_loader import load_tasks


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SEED_DATASET = PROJECT_ROOT / "evals" / "datasets" / "capability" / "b2b_recruiting_meeting_assistant.json"


class RunLayoutTests(unittest.TestCase):
    def setUp(self) -> None:
        self.task = load_tasks(SEED_DATASET)[0]

    def test_default_run_id_has_a_timestamp_and_task_suffix(self) -> None:
        run_id = _default_run_id((self.task,), False)
        self.assertRegex(run_id, rf"^\d{{8}}-\d{{6}}-{re.escape(self.task.id)}$")

    def test_runner_writes_the_summary_under_the_run_directory(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = io.StringIO()
            with redirect_stdout(output):
                exit_code = main(
                    [
                        "--datasets",
                        str(SEED_DATASET),
                        "--runs-root",
                        str(root),
                        "--run-id",
                        "layout-check",
                    ]
                )
            run_dir = root / "layout-check"
            self.assertEqual(exit_code, 1)
            self.assertTrue((run_dir / "summary.json").is_file())
            self.assertIn(f"Run directory: {run_dir}", output.getvalue())

    def test_runner_refuses_an_existing_run_directory(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "layout-check").mkdir()
            with self.assertRaises(SystemExit):
                main(
                    [
                        "--datasets",
                        str(SEED_DATASET),
                        "--runs-root",
                        str(root),
                        "--run-id",
                        "layout-check",
                        "--agent-command",
                        f"{sys.executable} -c pass",
                    ]
                )

    def test_runner_does_not_write_to_the_product_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            workspace = root / "workspace"
            workspace.mkdir()
            output = io.StringIO()
            with redirect_stdout(output):
                main(
                    [
                        "--datasets",
                        str(SEED_DATASET),
                        "--runs-root",
                        str(root / "runs"),
                        "--run-id",
                        "run",
                        "--agent-command",
                        f"{sys.executable} -c pass",
                    ]
                )
            self.assertEqual(list(workspace.iterdir()), [])
            self.assertTrue((root / "runs" / "run" / "trials" / self.task.id / "input.json").is_file())


if __name__ == "__main__":
    unittest.main()
