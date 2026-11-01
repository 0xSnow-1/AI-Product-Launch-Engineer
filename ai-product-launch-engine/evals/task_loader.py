"""JSON dataset discovery and validation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

from evals.models import DatasetValidationError, EvaluationTask


def dataset_files(dataset_path: Path) -> tuple[Path, ...]:
    """Return JSON task files in deterministic lexical order."""

    if dataset_path.is_file():
        if dataset_path.suffix != ".json":
            raise ValueError(f"Dataset file must use the .json extension: {dataset_path}")
        return (dataset_path,)
    if not dataset_path.is_dir():
        raise ValueError(f"Dataset path does not exist: {dataset_path}")

    files = tuple(sorted(path for path in dataset_path.rglob("*.json") if path.is_file()))
    if not files:
        raise ValueError(f"No JSON files found in: {dataset_path}")
    return files


def load_tasks(dataset_path: Path) -> tuple[EvaluationTask, ...]:
    """Load and validate all JSON task records under a file or directory."""

    tasks: list[EvaluationTask] = []
    task_ids: dict[str, EvaluationTask] = {}
    for file_path in dataset_files(dataset_path):
        try:
            raw: Any = json.loads(file_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            raise DatasetValidationError(file_path, error.lineno, f"invalid JSON: {error.msg}") from error
        if not isinstance(raw, dict):
            raise DatasetValidationError(file_path, 1, "each task file must contain an object")
        task = EvaluationTask.from_mapping(raw, file_path, 1)
        previous = task_ids.get(task.id)
        if previous is not None:
            raise DatasetValidationError(
                file_path,
                1,
                f"duplicate id {task.id!r}; first defined at {previous.source}",
            )
        task_ids[task.id] = task
        tasks.append(task)
    if not tasks:
        raise ValueError(f"No task records found in: {dataset_path}")
    return tuple(tasks)


def select_tasks(
    tasks: Iterable[EvaluationTask],
    task_ids: Iterable[str] = (),
    include_holdouts: bool = False,
) -> tuple[EvaluationTask, ...]:
    """Filter tasks without changing the source dataset."""

    available = {task.id: task for task in tasks}
    requested = tuple(task_ids)
    if requested:
        unknown = sorted(set(requested).difference(available))
        if unknown:
            raise ValueError(f"Unknown task ids: {', '.join(unknown)}")
        return tuple(available[task_id] for task_id in requested)
    selected = tuple(task for task in tasks if include_holdouts or not task.holdout)
    if not selected:
        raise ValueError("No tasks selected. Use --include-holdouts to run holdout tasks.")
    return selected
