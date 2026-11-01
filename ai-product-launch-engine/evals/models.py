"""Validated boundary models for evaluation datasets."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping


TASK_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]*$")
PROJECT_SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
VALID_SUITES = frozenset({"capability", "regression"})
REQUIRED_MANIFEST_AGENTS = frozenset(
    {"market_researcher", "customer_researcher", "gtm_strategist", "supervisor"}
)


class DatasetValidationError(ValueError):
    """A dataset record does not satisfy the evaluation contract."""

    def __init__(self, source: Path, line_number: int, message: str) -> None:
        super().__init__(f"{source}:{line_number}: {message}")
        self.source = source
        self.line_number = line_number


def required_artifact_paths(project_slug: str) -> tuple[str, ...]:
    """Return the canonical virtual artifact paths for one project."""

    root = f"/projects/{project_slug}"
    return (
        f"{root}/research/market.md",
        f"{root}/research/customers.md",
        f"{root}/strategy/gtm.md",
        f"{root}/blueprint.md",
        f"{root}/manifest.json",
        f"{root}/deliverable.zip",
    )


def _error(source: Path, line_number: int, message: str) -> DatasetValidationError:
    return DatasetValidationError(source, line_number, message)


def _string(value: Any, field: str, source: Path, line_number: int) -> str:
    if not isinstance(value, str) or not value.strip():
        raise _error(source, line_number, f"{field} must be a non-empty string")
    return value.strip()


def _mapping(value: Any, field: str, source: Path, line_number: int) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise _error(source, line_number, f"{field} must be an object")
    return value


def _string_tuple(value: Any, field: str, source: Path, line_number: int) -> tuple[str, ...]:
    if not isinstance(value, list) or not value:
        raise _error(source, line_number, f"{field} must be a non-empty list")
    strings = tuple(_string(item, field, source, line_number) for item in value)
    if len(strings) != len(set(strings)):
        raise _error(source, line_number, f"{field} must not contain duplicates")
    return strings


@dataclass(frozen=True)
class TaskInput:
    """User input given to the launch agent."""

    idea: str
    audience: str
    constraints: Mapping[str, str]


@dataclass(frozen=True)
class TaskExpectation:
    """Deterministic artifacts and sections required for a task."""

    project_slug: str
    artifacts: tuple[str, ...]
    required_sections: Mapping[str, tuple[str, ...]]
    min_sources: int
    manifest_agents: tuple[str, ...]


@dataclass(frozen=True)
class EvaluationTask:
    """One validated JSON task record."""

    id: str
    suite: str
    holdout: bool
    description: str
    input: TaskInput
    expected: TaskExpectation
    guardrails: tuple[str, ...]
    tracked_metrics: tuple[str, ...]
    source: Path
    line_number: int

    @classmethod
    def from_mapping(
        cls,
        raw: Mapping[str, Any],
        source: Path,
        line_number: int,
    ) -> "EvaluationTask":
        """Validate one decoded JSON object."""

        identifier = _string(raw.get("id"), "id", source, line_number)
        if not TASK_ID_PATTERN.fullmatch(identifier):
            raise _error(source, line_number, "id must use lowercase letters, digits, hyphens, or underscores")

        suite = _string(raw.get("suite"), "suite", source, line_number)
        if suite not in VALID_SUITES:
            raise _error(source, line_number, f"suite must be one of: {', '.join(sorted(VALID_SUITES))}")

        holdout = raw.get("holdout")
        if not isinstance(holdout, bool):
            raise _error(source, line_number, "holdout must be a boolean")

        description = _string(raw.get("description"), "description", source, line_number)
        input_data = _mapping(raw.get("input"), "input", source, line_number)
        idea = _string(input_data.get("idea"), "input.idea", source, line_number)
        audience = _string(input_data.get("audience"), "input.audience", source, line_number)
        if len(idea) > 500:
            raise _error(source, line_number, "input.idea must contain at most 500 characters")
        if len(audience) > 200:
            raise _error(source, line_number, "input.audience must contain at most 200 characters")
        raw_constraints = _mapping(input_data.get("constraints", {}), "input.constraints", source, line_number)
        constraints = {
            _string(key, "input.constraints key", source, line_number): _string(
                value,
                "input.constraints value",
                source,
                line_number,
            )
            for key, value in raw_constraints.items()
        }

        expected_data = _mapping(raw.get("expected"), "expected", source, line_number)
        project_slug = _string(expected_data.get("project_slug"), "expected.project_slug", source, line_number)
        if not PROJECT_SLUG_PATTERN.fullmatch(project_slug):
            raise _error(source, line_number, "expected.project_slug must use lowercase hyphenated words")

        artifacts = _string_tuple(expected_data.get("artifacts"), "expected.artifacts", source, line_number)
        canonical_artifacts = set(required_artifact_paths(project_slug))
        missing_artifacts = sorted(canonical_artifacts.difference(artifacts))
        if missing_artifacts:
            raise _error(source, line_number, f"expected.artifacts is missing: {', '.join(missing_artifacts)}")
        if any(not path.startswith(f"/projects/{project_slug}/") for path in artifacts):
            raise _error(source, line_number, "expected.artifacts must use canonical /projects/{project_slug}/ paths")

        raw_sections = _mapping(expected_data.get("required_sections"), "expected.required_sections", source, line_number)
        required_sections: dict[str, tuple[str, ...]] = {}
        for artifact_path, sections in raw_sections.items():
            artifact = _string(artifact_path, "expected.required_sections key", source, line_number)
            if artifact not in artifacts or not artifact.endswith(".md"):
                raise _error(source, line_number, "expected.required_sections keys must be expected Markdown artifact paths")
            required_sections[artifact] = _string_tuple(
                sections,
                f"expected.required_sections[{artifact}]",
                source,
                line_number,
            )
        if not required_sections:
            raise _error(source, line_number, "expected.required_sections must not be empty")

        min_sources = expected_data.get("min_sources")
        if isinstance(min_sources, bool) or not isinstance(min_sources, int) or min_sources < 3:
            raise _error(source, line_number, "expected.min_sources must be an integer of at least 3")

        manifest_agents = _string_tuple(
            expected_data.get("manifest_agents"),
            "expected.manifest_agents",
            source,
            line_number,
        )
        missing_agents = REQUIRED_MANIFEST_AGENTS.difference(manifest_agents)
        if missing_agents:
            raise _error(source, line_number, f"expected.manifest_agents is missing: {', '.join(sorted(missing_agents))}")

        return cls(
            id=identifier,
            suite=suite,
            holdout=holdout,
            description=description,
            input=TaskInput(idea=idea, audience=audience, constraints=constraints),
            expected=TaskExpectation(
                project_slug=project_slug,
                artifacts=artifacts,
                required_sections=required_sections,
                min_sources=min_sources,
                manifest_agents=manifest_agents,
            ),
            guardrails=_string_tuple(raw.get("guardrails"), "guardrails", source, line_number),
            tracked_metrics=_string_tuple(raw.get("tracked_metrics"), "tracked_metrics", source, line_number),
            source=source,
            line_number=line_number,
        )
