"""Supervisor factory and command-line entry point."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Sequence, TextIO

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


def _chunk_text(message: Any) -> str:
    """Return visible text from a streamed LangChain message chunk."""

    content = getattr(message, "content", "")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(
            item.get("text", "") if isinstance(item, dict) else str(item)
            for item in content
        )
    return ""


def stream_response(agent: Any, agent_input: dict[str, object], config: dict[str, object], output: TextIO) -> None:
    """Stream task events and response text so a live run never looks idle."""

    print("[progress] Starting supervisor.", file=output, flush=True)
    print("[progress] Waiting for Bedrock. The first response can take several minutes.", file=output, flush=True)
    printed_text = False
    for mode, payload in agent.stream(
        agent_input,
        config=config,
        stream_mode=["messages", "tasks"],
    ):
        if mode == "tasks":
            print("[progress] Task event received.", file=output, flush=True)
            continue
        if mode != "messages":
            continue
        message, _metadata = payload
        text = _chunk_text(message)
        if text:
            print(text, end="", file=output, flush=True)
            printed_text = True
    if printed_text:
        print(file=output, flush=True)
    print("[progress] Run completed.", file=output, flush=True)


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
    stream_response(
        build_supervisor(settings),
        agent_input,
        {"callbacks": callbacks},
        sys.stdout,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
