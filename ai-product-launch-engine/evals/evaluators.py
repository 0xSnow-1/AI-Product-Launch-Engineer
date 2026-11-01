"""Deterministic graders for completed evaluation trials."""

from __future__ import annotations

import json
import re
import zipfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping
from urllib.parse import urlparse

from evals.models import EvaluationTask


PLACEHOLDER_PATTERN = re.compile(r"\bTODO\b|\blorem ipsum\b|\[citation needed\]", re.IGNORECASE)
SOURCE_PATTERN = re.compile(r"^\s*[-*]\s+\[([^\]]*)]\(([^\s)]+)\)\s*$", re.MULTILINE)


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
            if not virtual_path.endswith(".md"):
                continue
            physical_path = _physical_path(trial_root, virtual_path)
            if not physical_path.is_file():
                continue
            content = physical_path.read_text(encoding="utf-8")
            for title, url in SOURCE_PATTERN.findall(content):
                if title.strip() and self._valid_url(url):
                    citations.append((title.strip(), url))
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


class PlaceholderGrader:
    """Reject placeholders that make a completed artifact unusable."""

    name = "placeholders"

    def grade(self, task: EvaluationTask, trial_root: Path) -> GradingResult:
        matches: dict[str, list[str]] = {}
        for virtual_path in task.expected.artifacts:
            if not virtual_path.endswith(".md"):
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
    SectionCoverageGrader(),
    SourceCitationGrader(),
    ManifestGrader(),
    ArchiveGrader(),
    PlaceholderGrader(),
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
