"""Run an external launch-agent command inside an isolated evaluation trial."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Mapping, Sequence

from evals.models import EvaluationTask


@dataclass(frozen=True)
class ExecutionResult:
    """The process outcome captured for one trial."""

    command: tuple[str, ...]
    returncode: int
    stdout: str
    stderr: str


def _timestamp() -> str:
    return datetime.now(UTC).isoformat()


def _write_event(transcript_path: Path, event: Mapping[str, object]) -> None:
    with transcript_path.open("a", encoding="utf-8") as transcript:
        transcript.write(f"{json.dumps(event, sort_keys=True)}\n")


def _copy_fixtures(task: EvaluationTask, fixture_root: Path, destination: Path) -> None:
    for fixture in task.fixtures:
        source = (fixture_root / fixture.path).resolve()
        root = fixture_root.resolve()
        if root not in source.parents or not source.is_file():
            raise ValueError(f"Fixture does not exist under fixture root: {fixture.path}")
        target = destination / fixture.path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)


def execute_task(
    task: EvaluationTask,
    trial_collection_root: Path,
    command: Sequence[str],
    fixture_root: Path,
    *,
    cwd: Path | None = None,
) -> ExecutionResult:
    """Execute a user-supplied agent command without using a model directly.

    The command receives the input and isolated trial paths through environment
    variables. It must write artifacts below ``LAUNCH_ENGINE_TRIAL_ROOT``.
    """

    if not command:
        raise ValueError("agent command must not be empty")
    collection_root = trial_collection_root.resolve()
    collection_root.mkdir(parents=True, exist_ok=True)
    trial_root = (collection_root / task.id).resolve()
    if collection_root not in trial_root.parents:
        raise ValueError("trial path must stay under the trial collection root")
    if trial_root.exists():
        raise FileExistsError(f"trial already exists: {trial_root}")
    trial_root.mkdir(parents=True)

    input_path = trial_root / "input.json"
    input_path.write_text(
        json.dumps(
            {
                "idea": task.input.idea,
                "audience": task.input.audience,
                "constraints": dict(task.input.constraints),
                "fixtures": [
                    {"path": f"/fixtures/{fixture.path}", "purpose": fixture.purpose}
                    for fixture in task.fixtures
                ],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    trial_fixture_root = trial_root / "fixtures"
    _copy_fixtures(task, fixture_root, trial_fixture_root)
    transcript_path = trial_root / "transcript.jsonl"
    _write_event(transcript_path, {"event": "trial_started", "timestamp": _timestamp(), "task_id": task.id})

    environment = os.environ.copy()
    environment.update(
        {
            "LAUNCH_ENGINE_INPUT_PATH": str(input_path),
            "LAUNCH_ENGINE_TRIAL_ROOT": str(trial_root),
            "LAUNCH_ENGINE_FIXTURE_ROOT": str(trial_fixture_root),
            "LAUNCH_ENGINE_TRANSCRIPT_PATH": str(transcript_path),
        }
    )
    completed = subprocess.run(
        tuple(command),
        cwd=cwd,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
    )
    result = ExecutionResult(
        command=tuple(command),
        returncode=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )
    _write_event(
        transcript_path,
        {
            "event": "agent_finished",
            "timestamp": _timestamp(),
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        },
    )
    return result
