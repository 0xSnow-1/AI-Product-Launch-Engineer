"""Build the launch deliverable manifest and archive."""

from __future__ import annotations

import json
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping, Sequence


MANIFEST_VERSION = "1.0.0"
MANIFEST_ARTIFACTS = ("market.md", "customers.md", "gtm.md", "blueprint.md", "manifest.json")
ARCHIVE_ENTRIES = (
    "research/market.md",
    "research/customers.md",
    "strategy/gtm.md",
    "blueprint.md",
    "manifest.json",
)


def write_manifest(
    project_root: Path,
    project_slug: str,
    agents_used: Sequence[str],
    metrics: Mapping[str, Any],
) -> Path:
    """Write manifest.json for one launch project."""

    manifest = {
        "metadata": {
            "project_slug": project_slug,
            "created_at": datetime.now(UTC).isoformat(),
            "version": MANIFEST_VERSION,
        },
        "artifacts": list(MANIFEST_ARTIFACTS),
        "execution": {
            "agents_used": list(agents_used),
            "total_turns": int(metrics.get("total_turns") or 0),
            "total_tool_calls": int(metrics.get("total_tool_calls") or 0),
            "total_tokens": int(metrics.get("total_tokens") or 0),
        },
    }
    project_root.mkdir(parents=True, exist_ok=True)
    manifest_path = project_root / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest_path


def build_deliverable(project_root: Path, project_slug: str) -> Path:
    """Build deliverable.zip from the five non-archive project files."""

    archive_path = project_root / "deliverable.zip"
    with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for entry in ARCHIVE_ENTRIES:
            source = project_root / entry
            if not source.is_file():
                raise FileNotFoundError(f"Missing deliverable file for archive: {entry}")
            archive.write(source, arcname=entry)
    return archive_path
