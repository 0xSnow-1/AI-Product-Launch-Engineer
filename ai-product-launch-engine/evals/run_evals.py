"""Validate datasets and grade completed evaluation trials."""

from __future__ import annotations

import argparse
import json
import shlex
from pathlib import Path
from typing import Sequence

from evals.executor import execute_task
from evals.evaluators import EvaluationReport, grade_trial
from evals.models import DatasetValidationError, EvaluationTask
from evals.task_loader import load_tasks, select_tasks


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--datasets",
        type=Path,
        default=Path("evals/datasets"),
        help="A JSON task file or a directory of JSON task files.",
    )
    parser.add_argument(
        "--trial-root",
        type=Path,
        help="Directory containing one isolated workspace per task id.",
    )
    parser.add_argument("--task", action="append", default=[], help="Evaluate one task id. Repeat to select several tasks.")
    parser.add_argument("--include-holdouts", action="store_true", help="Include holdout tasks in an unfiltered run.")
    parser.add_argument("--validate-only", action="store_true", help="Validate JSON task files without grading trial artifacts.")
    parser.add_argument("--report", type=Path, help="Write the JSON report to this path instead of standard output.")
    parser.add_argument(
        "--agent-command",
        help="Run this command once per selected task before grading. The command receives LAUNCH_ENGINE_* paths in its environment.",
    )
    parser.add_argument(
        "--fixture-root",
        type=Path,
        default=Path("evals/fixtures"),
        help="Directory containing controlled JSON source fixtures.",
    )
    return parser


def evaluate(tasks: Sequence[EvaluationTask], trial_root: Path) -> tuple[EvaluationReport, ...]:
    """Grade each task in its own trial directory."""

    reports = tuple(grade_trial(task, trial_root / task.id) for task in tasks)
    for report in reports:
        if report.trial_root.is_dir():
            report_path = report.trial_root / "grader_results.json"
            report_path.write_text(json.dumps(report.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return reports


def _write_report(report: dict[str, object], output_path: Path | None) -> None:
    serialized = json.dumps(report, indent=2, sort_keys=True)
    if output_path is None:
        print(serialized)
        return
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(f"{serialized}\n", encoding="utf-8")


def main(argv: Sequence[str] | None = None) -> int:
    """Run dataset validation or deterministic trial grading."""

    parser = _parser()
    args = parser.parse_args(argv)
    try:
        tasks = load_tasks(args.datasets)
        selected = select_tasks(tasks, args.task, args.include_holdouts)
    except (DatasetValidationError, ValueError) as error:
        parser.error(str(error))

    if args.validate_only:
        _write_report(
            {
                "dataset_files": sorted({str(task.source) for task in selected}),
                "task_count": len(selected),
                "task_ids": [task.id for task in selected],
                "valid": True,
            },
            args.report,
        )
        return 0

    if args.trial_root is None:
        parser.error("--trial-root is required unless --validate-only is set")
    execution_results: list[dict[str, object]] = []
    if args.agent_command:
        try:
            command = shlex.split(args.agent_command)
            for task in selected:
                result = execute_task(task, args.trial_root, command, args.fixture_root)
                execution_results.append(
                    {"task_id": task.id, "returncode": result.returncode, "command": list(result.command)}
                )
        except (FileExistsError, OSError, ValueError) as error:
            parser.error(str(error))
    reports = evaluate(selected, args.trial_root)
    payload = {
        "passed": all(report.passed for report in reports),
        "reports": [report.to_dict() for report in reports],
        "executions": execution_results,
    }
    report_path = args.report
    if report_path is None and args.agent_command:
        report_path = args.trial_root.parent / "summary.json"
    _write_report(payload, report_path)
    return 0 if payload["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
