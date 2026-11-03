"""Run the launch-engine command-line interface from the project root."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Sequence

from dotenv import load_dotenv


sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Create an evidence-backed product launch blueprint.")
    parser.add_argument("--input", type=Path, help="Path to a launch request JSON file.")
    parser.add_argument("--workspace-root", type=Path, help="Physical root for this invocation's virtual filesystem.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    load_dotenv()
    args = _parser().parse_args(argv)
    if args.workspace_root is not None:
        os.environ["WORKSPACE_ROOT"] = str(args.workspace_root)

    from agents.supervisor import create_blueprint, stream_response, supervisor
    from src.config import Settings
    from src.metrics import collect_metrics
    from workflows.packaging import build_deliverable, write_manifest
    from src.schemas import LaunchRequest
    from src.transcript import JsonlCallbackHandler
    from src.workflows.validation import ArtifactValidationError, validate_project

    input_path = args.input or (
        Path(os.environ["LAUNCH_ENGINE_INPUT_PATH"]) if "LAUNCH_ENGINE_INPUT_PATH" in os.environ else None
    )
    if input_path is None:
        raise SystemExit("--input or LAUNCH_ENGINE_INPUT_PATH is required")

    raw_request = json.loads(input_path.read_text(encoding="utf-8"))
    request = LaunchRequest.from_mapping(raw_request)
    callbacks = []
    if "LAUNCH_ENGINE_TRANSCRIPT_PATH" in os.environ:
        callbacks.append(JsonlCallbackHandler(Path(os.environ["LAUNCH_ENGINE_TRANSCRIPT_PATH"])))
    agent_input = {
        "messages": [
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "idea": request.idea,
                        "audience": request.audience,
                        "constraints": dict(request.constraints),
                        "project_slug": request.project_slug,
                        "controlled_fixtures": raw_request.get("fixtures", []),
                    }
                ),
            }
        ]
    }

    settings = Settings.from_environment(project_root=Path(__file__).resolve().parent)
    workspace_root = args.workspace_root if args.workspace_root is not None else settings.workspace_root
    project_root = workspace_root / "projects" / request.project_slug

    stream_response(supervisor, agent_input, {"callbacks": callbacks}, sys.stdout)

    try:
        validate_project(project_root)
    except ArtifactValidationError as error:
        raise SystemExit(f"artifact validation failed: {error}") from error
    create_blueprint(supervisor, request.project_slug, workspace_root, sys.stdout)

    metrics = collect_metrics()
    write_manifest(project_root, request.project_slug, list(metrics.get("agents_used") or []), metrics)
    build_deliverable(project_root, request.project_slug)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
