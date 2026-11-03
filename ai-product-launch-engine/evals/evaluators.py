"""Deterministic graders for completed evaluation trials."""

from __future__ import annotations

import ast
import json
import re
import zipfile
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable, Mapping
from urllib.parse import urlparse

from evals.models import EvaluationTask
from src.workflows.validation import ArtifactKind, ArtifactValidationError, load_artifact


PLACEHOLDER_PATTERN = re.compile(r"\bTODO\b|\blorem ipsum\b|\[citation needed\]", re.IGNORECASE)

SCHEMA_ARTIFACT_KINDS: dict[str, ArtifactKind] = {
    "research/market_research.json": "market_research",
    "research/customer_research.json": "customer_research",
    "strategy/gtm_strategy.json": "gtm_strategy",
}


@dataclass(frozen=True)
class GradingResult:
    """Outcome of one deterministic grader."""

    grader_name: str
    passed: bool
    score: float
    details: Mapping[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class EvaluationReport:
    """All deterministic grading results for a completed trial."""

    task_id: str
    trial_root: Path
    results: tuple[GradingResult, ...]

    @property
    def passed(self) -> bool:
        return all(result.passed for result in self.results)

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "trial_root": str(self.trial_root),
            "passed": self.passed,
            "results": [result.to_dict() for result in self.results],
        }


def _physical_path(trial_root: Path, virtual_path: str) -> Path:
    """Map a contract virtual path to a safe path inside one trial root."""

    if not virtual_path.startswith("/"):
        raise ValueError(f"Virtual path must be absolute: {virtual_path}")
    root = trial_root.resolve()
    candidate = (root / virtual_path.lstrip("/")).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as error:
        raise ValueError(f"Virtual path escapes the trial root: {virtual_path}") from error
    return candidate


def _result(name: str, passed: bool, details: Mapping[str, Any]) -> GradingResult:
    return GradingResult(grader_name=name, passed=passed, score=1.0 if passed else 0.0, details=details)


class ArtifactExistsGrader:
    """Require every expected artifact at its exact virtual path."""

    name = "artifact_exists"

    def grade(self, task: EvaluationTask, trial_root: Path) -> GradingResult:
        missing = [
            path for path in task.expected.artifacts if not _physical_path(trial_root, path).is_file()
        ]
        return _result(self.name, not missing, {"missing_artifacts": missing})


class DeprecatedPathGrader:
    """Reject the legacy virtual path that caused the doubled-path defect."""

    name = "deprecated_path"

    def grade(self, task: EvaluationTask, trial_root: Path) -> GradingResult:
        deprecated_root = _physical_path(trial_root, "/workspace/research")
        return _result(
            self.name,
            not deprecated_root.exists(),
            {"deprecated_path": "/workspace/research", "exists": deprecated_root.exists()},
        )


class ArtifactSchemaGrader:
    """Validate the specialist JSON artifacts against the product contracts."""

    name = "artifact_schemas"

    def grade(self, task: EvaluationTask, trial_root: Path) -> GradingResult:
        slug = task.expected.project_slug
        project_root = _physical_path(trial_root, f"/projects/{slug}")
        expected_relatives = {
            virtual_path.removeprefix(f"/projects/{slug}/")
            for virtual_path in task.expected.artifacts
            if virtual_path.startswith(f"/projects/{slug}/")
        }
        errors: dict[str, str] = {}
        for relative, kind in SCHEMA_ARTIFACT_KINDS.items():
            if relative not in expected_relatives:
                continue
            try:
                load_artifact(project_root, kind)
            except ArtifactValidationError as error:
                errors[relative] = str(error)
        return _result(self.name, not errors, {"schema_errors": errors})


class SectionCoverageGrader:
    """Require exact Markdown headings defined by the task."""

    name = "section_coverage"

    @staticmethod
    def _has_heading(content: str, heading: str) -> bool:
        pattern = re.compile(rf"^#{{1,6}}\s+{re.escape(heading)}\s*#*\s*$", re.IGNORECASE | re.MULTILINE)
        return pattern.search(content) is not None

    def grade(self, task: EvaluationTask, trial_root: Path) -> GradingResult:
        missing: dict[str, list[str]] = {}
        for virtual_path, headings in task.expected.required_sections.items():
            physical_path = _physical_path(trial_root, virtual_path)
            if not physical_path.is_file():
                missing[virtual_path] = list(headings)
                continue
            content = physical_path.read_text(encoding="utf-8")
            absent = [heading for heading in headings if not self._has_heading(content, heading)]
            if absent:
                missing[virtual_path] = absent
        return _result(self.name, not missing, {"missing_sections": missing})


def _iter_evidence_refs(node: Any) -> Iterable[Mapping[str, Any]]:
    """Yield every evidence-ref-shaped object inside a parsed JSON artifact."""

    if isinstance(node, Mapping):
        if isinstance(node.get("title"), str) and isinstance(node.get("url"), str):
            yield node
        for value in node.values():
            yield from _iter_evidence_refs(value)
    elif isinstance(node, list):
        for item in node:
            yield from _iter_evidence_refs(item)


class SourceCitationGrader:
    """Require a task-defined minimum of titled HTTP or HTTPS citations."""

    name = "source_citations"

    @staticmethod
    def _valid_url(url: str) -> bool:
        parsed = urlparse(url)
        return parsed.scheme in {"http", "https"} and bool(parsed.netloc)

    def grade(self, task: EvaluationTask, trial_root: Path) -> GradingResult:
        citations: list[tuple[str, str]] = []
        invalid_urls: list[str] = []
        for virtual_path in task.expected.artifacts:
            if not virtual_path.endswith(".json") or virtual_path.endswith("manifest.json"):
                continue
            physical_path = _physical_path(trial_root, virtual_path)
            if not physical_path.is_file():
                continue
            try:
                parsed = json.loads(physical_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                invalid_urls.append(f"{virtual_path}: unreadable JSON")
                continue
            for ref in _iter_evidence_refs(parsed):
                title = str(ref["title"]).strip()
                url = str(ref["url"]).strip()
                if title and self._valid_url(url):
                    citations.append((title, url))
                else:
                    invalid_urls.append(url)
        unique_citations = {(title, url) for title, url in citations}
        passed = len(unique_citations) >= task.expected.min_sources and not invalid_urls
        return _result(
            self.name,
            passed,
            {
                "required_sources": task.expected.min_sources,
                "unique_source_count": len(unique_citations),
                "invalid_urls": invalid_urls,
            },
        )


class ManifestGrader:
    """Validate the manifest shape required by the evaluation contract."""

    name = "manifest"

    def grade(self, task: EvaluationTask, trial_root: Path) -> GradingResult:
        manifest_path = _physical_path(trial_root, f"/projects/{task.expected.project_slug}/manifest.json")
        if not manifest_path.is_file():
            return _result(self.name, False, {"error": "manifest is missing"})
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            return _result(self.name, False, {"error": f"invalid JSON: {error.msg}"})
        if not isinstance(manifest, dict):
            return _result(self.name, False, {"error": "manifest root must be an object"})

        errors: list[str] = []
        metadata = manifest.get("metadata")
        if not isinstance(metadata, dict):
            errors.append("metadata must be an object")
        else:
            if metadata.get("project_slug") != task.expected.project_slug:
                errors.append("metadata.project_slug does not match the task")
            if not isinstance(metadata.get("created_at"), str) or not metadata["created_at"].strip():
                errors.append("metadata.created_at must be a non-empty string")
            if not isinstance(metadata.get("version"), str) or not metadata["version"].strip():
                errors.append("metadata.version must be a non-empty string")

        artifacts = manifest.get("artifacts")
        required_names = {Path(path).name for path in task.expected.artifacts if not path.endswith(".zip")}
        if (
            not isinstance(artifacts, list)
            or not all(isinstance(artifact, str) for artifact in artifacts)
            or not required_names.issubset(set(artifacts))
        ):
            errors.append("artifacts must list each required non-archive artifact name")

        execution = manifest.get("execution")
        if not isinstance(execution, dict):
            errors.append("execution must be an object")
        else:
            agents_used = execution.get("agents_used")
            if (
                not isinstance(agents_used, list)
                or not all(isinstance(agent, str) for agent in agents_used)
                or not set(task.expected.manifest_agents).issubset(set(agents_used))
            ):
                errors.append("execution.agents_used is incomplete")
            for metric in ("total_turns", "total_tool_calls", "total_tokens"):
                value = execution.get(metric)
                if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                    errors.append(f"execution.{metric} must be a non-negative integer")
        return _result(self.name, not errors, {"errors": errors})


class ArchiveGrader:
    """Require a valid ZIP archive that contains the required deliverables."""

    name = "archive"

    def grade(self, task: EvaluationTask, trial_root: Path) -> GradingResult:
        archive_path = _physical_path(trial_root, f"/projects/{task.expected.project_slug}/deliverable.zip")
        if not archive_path.is_file() or not zipfile.is_zipfile(archive_path):
            return _result(self.name, False, {"error": "deliverable.zip is missing or invalid"})
        expected_entries = {
            path.removeprefix(f"/projects/{task.expected.project_slug}/")
            for path in task.expected.artifacts
            if not path.endswith(".zip")
        }
        try:
            with zipfile.ZipFile(archive_path) as archive:
                corrupted_entry = archive.testzip()
                entries = set(archive.namelist())
        except (OSError, zipfile.BadZipFile) as error:
            return _result(self.name, False, {"error": f"cannot read archive: {error}"})
        if corrupted_entry is not None:
            return _result(self.name, False, {"error": f"corrupt archive entry: {corrupted_entry}"})
        missing_entries = sorted(expected_entries.difference(entries))
        return _result(self.name, not missing_entries, {"missing_entries": missing_entries})


def _parse_timestamp(value: Any) -> datetime | None:
    """Parse an ISO 8601 timestamp and normalize it to UTC."""

    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed


def _format_timestamp(value: datetime | None) -> str | None:
    return value.isoformat() if value is not None else None


def _parse_tool_input(value: Any) -> Mapping[str, Any] | None:
    """Accept JSON input and Python dict string input."""

    if isinstance(value, Mapping):
        return value
    if not isinstance(value, str):
        return None
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        try:
            parsed = ast.literal_eval(value)
        except (ValueError, SyntaxError):
            return None
    return parsed if isinstance(parsed, Mapping) else None


class DelegationGrader:
    """Prove the subagent path and the GTM dependency from the transcript."""

    name = "delegation"
    _RESEARCH_SUBAGENTS = ("market_researcher", "customer_researcher")
    _GTM_SUBAGENT = "gtm_strategist"

    @staticmethod
    def _read_events(transcript_path: Path) -> tuple[list[tuple[int, Mapping[str, Any]]], list[dict[str, Any]]]:
        events: list[tuple[int, Mapping[str, Any]]] = []
        malformed: list[dict[str, Any]] = []
        for line_number, line in enumerate(transcript_path.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError as error:
                malformed.append({"line": line_number, "error": error.msg})
                continue
            if not isinstance(event, Mapping):
                malformed.append({"line": line_number, "error": "event must be a JSON object"})
                continue
            events.append((line_number, event))
        return events, malformed

    def grade(self, task: EvaluationTask, trial_root: Path) -> GradingResult:
        required = tuple(task.expected.required_subagents)
        details: dict[str, Any] = {
            "required_subagents": list(required),
            "max_tool_calls": task.expected.max_tool_calls,
        }
        transcript_path = trial_root / "transcript.jsonl"
        if not transcript_path.is_file():
            return _result(self.name, False, {**details, "error": "transcript.jsonl is missing"})
        try:
            events, malformed = self._read_events(transcript_path)
        except (OSError, UnicodeDecodeError) as error:
            return _result(self.name, False, {**details, "error": f"cannot read transcript: {error}"})
        if malformed:
            return _result(
                self.name,
                False,
                {**details, "error": "malformed transcript line", "malformed_lines": malformed},
            )

        starts: dict[str, dict[str, Any]] = {}
        finishes: dict[str, dict[str, Any]] = {}
        missing_run_id_lines: list[int] = []
        invalid_events: list[dict[str, Any]] = []
        research_writes: list[dict[str, Any]] = []
        tool_call_count = 0

        for line_number, event in events:
            kind = event.get("event")
            if kind == "tool_started":
                tool_call_count += 1
                tool = event.get("tool")
                if tool != "task":
                    input_data = _parse_tool_input(event.get("input"))
                    if input_data is not None:
                        serialized_input = json.dumps(input_data, sort_keys=True)
                        for path in ("research/market_research.json", "research/customer_research.json"):
                            if path in serialized_input:
                                research_writes.append({"line": line_number, "tool": tool, "path": path})

            is_task_start = kind == "tool_started" and event.get("tool") == "task"
            is_task_finish = kind == "tool_finished" and event.get("tool") == "task"
            is_explicit_start = kind == "delegation_started"
            is_explicit_finish = kind == "delegation_finished"
            if not (is_task_start or is_task_finish or is_explicit_start or is_explicit_finish):
                continue

            run_id = event.get("run_id")
            if run_id is None or not str(run_id).strip():
                missing_run_id_lines.append(line_number)
                continue
            run_key = str(run_id)

            if is_task_start or is_explicit_start:
                subagent: Any = event.get("subagent")
                if is_task_start:
                    input_data = _parse_tool_input(event.get("input"))
                    subagent = input_data.get("subagent_type") if input_data is not None else None
                if not isinstance(subagent, str) or not subagent.strip():
                    invalid_events.append({"line": line_number, "error": "subagent is missing"})
                    continue
                timestamp = _parse_timestamp(event.get("timestamp"))
                if timestamp is None:
                    invalid_events.append({"line": line_number, "error": "timestamp is missing or invalid"})
                    continue
                if run_key in starts:
                    invalid_events.append({"line": line_number, "error": f"duplicate start for run_id {run_key}"})
                    continue
                starts[run_key] = {"subagent": subagent.strip(), "timestamp": timestamp, "line": line_number}
                continue

            timestamp = _parse_timestamp(event.get("timestamp"))
            if timestamp is None:
                invalid_events.append({"line": line_number, "error": "timestamp is missing or invalid"})
                continue
            if run_key in finishes:
                invalid_events.append({"line": line_number, "error": f"duplicate finish for run_id {run_key}"})
                continue
            finishes[run_key] = {
                "subagent": event.get("subagent"),
                "timestamp": timestamp,
                "line": line_number,
            }

        start_times: dict[str, datetime] = {}
        finish_times: dict[str, datetime] = {}
        errors: list[str] = []

        for run_key, start in starts.items():
            subagent = start["subagent"]
            if subagent not in start_times or start["timestamp"] < start_times[subagent]:
                start_times[subagent] = start["timestamp"]
            finish = finishes.get(run_key)
            if finish is None:
                continue
            finish_subagent = finish.get("subagent") or subagent
            if finish_subagent != subagent:
                errors.append(f"run_id {run_key} pairs {subagent} with {finish_subagent}")
                continue
            if finish_subagent not in finish_times or finish["timestamp"] < finish_times[finish_subagent]:
                finish_times[finish_subagent] = finish["timestamp"]

        unpaired_finish_lines = sorted(
            finish["line"] for run_key, finish in finishes.items() if run_key not in starts
        )
        if unpaired_finish_lines:
            errors.append("finish event without a matching start run_id")

        if missing_run_id_lines:
            errors.append("missing run_id; delegation dependency cannot be proven")
        for invalid in invalid_events:
            errors.append(f"invalid delegation event on line {invalid['line']}: {invalid['error']}")

        delegated = sorted(start_times)
        missing = sorted(set(required).difference(start_times))
        if missing:
            errors.append("missing subagents: " + ", ".join(missing))

        market_finish = finish_times.get(self._RESEARCH_SUBAGENTS[0])
        customer_finish = finish_times.get(self._RESEARCH_SUBAGENTS[1])
        gtm_start = start_times.get(self._GTM_SUBAGENT)

        for name, finish_time in zip(self._RESEARCH_SUBAGENTS, (market_finish, customer_finish)):
            if name in required and finish_time is None:
                errors.append(f"missing finish for {name}")

        gtm_after_both_research = False
        if gtm_start is None:
            if self._GTM_SUBAGENT in required:
                errors.append("gtm_strategist did not start")
        elif market_finish is None or customer_finish is None:
            errors.append("gtm dependency cannot be proven because a research finish is missing")
        else:
            if gtm_start < market_finish:
                errors.append("gtm_strategist started before market_researcher finished")
            if gtm_start < customer_finish:
                errors.append("gtm_strategist started before customer_researcher finished")
            gtm_after_both_research = gtm_start >= market_finish and gtm_start >= customer_finish

        if tool_call_count > task.expected.max_tool_calls:
            errors.append(
                f"tool call count {tool_call_count} exceeds budget {task.expected.max_tool_calls}"
            )

        details.update(
            {
                "delegated_subagents": delegated,
                "missing_subagents": missing,
                "start_times": {name: _format_timestamp(start_times.get(name)) for name in required},
                "finish_times": {name: _format_timestamp(finish_times.get(name)) for name in required},
                "gtm_after_both_research": gtm_after_both_research,
                "tool_call_count": tool_call_count,
                "unfinished_subagents": sorted(set(start_times).difference(finish_times)),
                "missing_run_id_lines": missing_run_id_lines,
                "unpaired_finish_lines": unpaired_finish_lines,
                "invalid_delegation_events": invalid_events,
                "research_artifact_writes": research_writes,
                "errors": errors,
            }
        )
        return _result(self.name, not errors, details)


class PlaceholderGrader:
    """Reject placeholders that make a completed artifact unusable."""

    name = "placeholders"

    def grade(self, task: EvaluationTask, trial_root: Path) -> GradingResult:
        matches: dict[str, list[str]] = {}
        for virtual_path in task.expected.artifacts:
            if not (virtual_path.endswith(".md") or virtual_path.endswith(".json")):
                continue
            if virtual_path.endswith("manifest.json"):
                continue
            physical_path = _physical_path(trial_root, virtual_path)
            if not physical_path.is_file():
                continue
            found = sorted(set(PLACEHOLDER_PATTERN.findall(physical_path.read_text(encoding="utf-8"))))
            if found:
                matches[virtual_path] = found
        return _result(self.name, not matches, {"placeholders": matches})


DEFAULT_GRADERS = (
    ArtifactExistsGrader(),
    DeprecatedPathGrader(),
    ArtifactSchemaGrader(),
    SectionCoverageGrader(),
    SourceCitationGrader(),
    ManifestGrader(),
    ArchiveGrader(),
    PlaceholderGrader(),
    DelegationGrader(),
)


def grade_trial(
    task: EvaluationTask,
    trial_root: Path,
    graders: Iterable[object] = DEFAULT_GRADERS,
) -> EvaluationReport:
    """Run all deterministic graders against one isolated trial root."""

    root = trial_root.resolve()
    results = tuple(grader.grade(task, root) for grader in graders)
    return EvaluationReport(task_id=task.id, trial_root=root, results=results)
