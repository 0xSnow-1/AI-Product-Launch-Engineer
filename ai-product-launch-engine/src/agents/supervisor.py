"""Supervisor factory and command-line entry point."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Sequence

from dotenv import load_dotenv

from agents import customer_researcher, gtm_strategist, market_researcher
from agents.common import create_backend, create_model, create_search_tool, load_prompt
from src.config import Settings
from src.schemas import LaunchRequest
from src.transcript import JsonlCallbackHandler


def build_supervisor(settings: Settings):
    """Build the orchestrator with all three registered specialist agents."""

    from deepagents import create_deep_agent
    from langchain.agents.middleware import TodoListMiddleware

    model = create_model(settings)
    search_tool = create_search_tool()
    subagents = [
        market_researcher.definition(model, search_tool),
        customer_researcher.definition(model, search_tool),
        gtm_strategist.definition(model, search_tool),
    ]
    return create_deep_agent(
        model=model,
        backend=create_backend(settings),
        system_prompt=load_prompt("supervisor", "v2.yaml"),
        tools=[search_tool],
        middleware=[TodoListMiddleware()],
        subagents=subagents,
        name="product_launch_supervisor",
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Create an evidence-backed product launch blueprint.")
    parser.add_argument("--input", type=Path, help="Path to a launch request JSON file.")
    parser.add_argument("--workspace-root", type=Path, help="Physical root for this invocation's virtual filesystem.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run one real launch request. This is the only path that invokes a model."""

    load_dotenv()
    args = _parser().parse_args(argv)
    input_path = args.input or (Path(os.environ["LAUNCH_ENGINE_INPUT_PATH"]) if "LAUNCH_ENGINE_INPUT_PATH" in os.environ else None)
    if input_path is None:
        raise SystemExit("--input or LAUNCH_ENGINE_INPUT_PATH is required")
    workspace_root = args.workspace_root or (
        Path(os.environ["LAUNCH_ENGINE_TRIAL_ROOT"]) if "LAUNCH_ENGINE_TRIAL_ROOT" in os.environ else None
    )
    raw_request = json.loads(input_path.read_text(encoding="utf-8"))
    request = LaunchRequest.from_mapping(raw_request)
    settings = Settings.from_environment(project_root=Path(__file__).resolve().parents[2])
    if workspace_root is not None:
        settings = Settings(settings.bedrock_model_id, settings.bedrock_region, workspace_root)
    callbacks = []
    if "LAUNCH_ENGINE_TRANSCRIPT_PATH" in os.environ:
        callbacks.append(JsonlCallbackHandler(Path(os.environ["LAUNCH_ENGINE_TRANSCRIPT_PATH"])))
    result = build_supervisor(settings).invoke(
        {
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
        },
        config={"callbacks": callbacks},
    )
    print(result["messages"][-1].content)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
