"""Application configuration that does not perform provider calls at import time."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping


@dataclass(frozen=True)
class Settings:
    """Runtime settings for one launch-engine invocation."""

    bedrock_model_id: str
    bedrock_region: str
    workspace_root: Path

    @classmethod
    def from_environment(
        cls,
        environment: Mapping[str, str] | None = None,
        project_root: Path | None = None,
    ) -> "Settings":
        """Load settings without prompting for credentials or calling a provider."""

        values = os.environ if environment is None else environment
        root = project_root or Path(__file__).resolve().parents[1]
        configured_workspace = Path(values.get("WORKSPACE_ROOT", "workspace"))
        workspace_root = configured_workspace if configured_workspace.is_absolute() else root / configured_workspace
        return cls(
            bedrock_model_id=values.get("BEDROCK_MODEL_ID", "anthropic.claude-haiku-4-5-20251001-v1:0"),
            bedrock_region=values.get("BEDROCK_REGION", "us-east-1"),
            workspace_root=workspace_root,
        )
