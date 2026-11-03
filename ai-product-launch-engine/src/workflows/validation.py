"""Load and validate the JSON artifacts the specialist agents write."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

from pydantic import ValidationError

from src.contracts import CustomerResearch, GTMStrategy, MarketResearch

ArtifactKind = Literal["market_research", "customer_research", "gtm_strategy"]
Artifact = MarketResearch | CustomerResearch | GTMStrategy

ARTIFACT_SPECS: dict[ArtifactKind, tuple[str, type[Artifact]]] = {
    "market_research": ("research/market_research.json", MarketResearch),
    "customer_research": ("research/customer_research.json", CustomerResearch),
    "gtm_strategy": ("strategy/gtm_strategy.json", GTMStrategy),
}


class ArtifactValidationError(ValueError):
    """A specialist artifact is missing, malformed, or incomplete."""


def artifact_path(project_root: Path, kind: ArtifactKind) -> Path:
    """Return the canonical virtual path for one artifact under the project root."""

    relative, _ = ARTIFACT_SPECS[kind]
    return project_root / relative


def load_artifact(project_root: Path, kind: ArtifactKind) -> Artifact:
    """Parse one artifact with its contract model or raise a clear error."""

    relative, model = ARTIFACT_SPECS[kind]
    path = artifact_path(project_root, kind)
    if not path.is_file():
        raise ArtifactValidationError(f"missing artifact: {relative} (expected at {path})")
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ArtifactValidationError(f"malformed JSON in {relative}: {error.msg} (line {error.lineno})") from error
    if not isinstance(raw, dict):
        raise ArtifactValidationError(f"malformed artifact {relative}: root must be a JSON object")
    try:
        return model.model_validate(raw)
    except ValidationError as error:
        details = "; ".join(
            f"{'.'.join(str(part) for part in issue['loc'])}: {issue['msg']}" for issue in error.errors()
        )
        raise ArtifactValidationError(f"invalid artifact {relative}: {details}") from error


def validate_project(project_root: Path) -> dict[ArtifactKind, Artifact]:
    """Validate all three specialist artifacts. Raise on the first failure."""

    artifacts: dict[ArtifactKind, Artifact] = {}
    for kind in ARTIFACT_SPECS:
        artifacts[kind] = load_artifact(project_root, kind)
    return artifacts
