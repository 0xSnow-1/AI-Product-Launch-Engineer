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
    print("\n=== SUPERVISOR SUMMARY ===", file=output, flush=True)
    print(f"Project: {agent_input['messages'][0]['content']}", file=output, flush=True)


def _create_blueprint(agent: Any, project_slug: str, output: TextIO) -> None:
    """Create the final blueprint.md artifact synthesizing market, customer, and GTM research."""

    from pathlib import Path

    print("[progress] Creating blueprint.md from research artifacts...", file=output, flush=True)

    try:
        # Read the research artifacts
        market_path = Path(f"/projects/{project_slug}/research/market.md")
        customers_path = Path(f"/projects/{project_slug}/research/customers.md")
        gtm_path = Path(f"/projects/{project_slug}/strategy/gtm.md")

        # Read content if files exist
        artifacts = {}
        if market_path.exists():
            artifacts["market_research"] = market_path.read_text(encoding="utf-8")
        if customers_path.exists():
            artifacts["customer_research"] = customers_path.read_text(encoding="utf-8")
        if gtm_path.exists():
            artifacts["gtm_strategy"] = gtm_path.read_text(encoding="utf-8")

        # Get truncated content for each artifact
        market_content = artifacts.get("market_research", "")[:1000] if artifacts.get("market_research") else ""
        customer_content = artifacts.get("customer_research", "")[:1000] if artifacts.get("customer_research") else ""
        gtm_content = artifacts.get("gtm_strategy", "")[:1000] if artifacts.get("gtm_strategy") else ""

        # Create a comprehensive blueprint using list-based string construction
        blueprint_lines = [
            "# Product Launch Blueprint",
            "",
            f"## Project: {project_slug}",
            f"Generated: {Path.cwd()}",
            "",
            "## Executive Summary",
            "This blueprint synthesizes market research, customer insights, and go-to-market strategy to provide a comprehensive launch plan.",
            "",
            "## Market Research"
        ]

        if market_content:
            blueprint_lines.append(market_content + "...")
        else:
            blueprint_lines.append("No market research available")

        blueprint_lines.extend(["", "## Customer Research"])

        if customer_content:
            blueprint_lines.append(customer_content + "...")
        else:
            blueprint_lines.append("No customer research available")

        blueprint_lines.extend(["", "## GTM Strategy"])

        if gtm_content:
            blueprint_lines.append(gtm_content + "...")
        else:
            blueprint_lines.append("No GTM strategy available")

        blueprint_lines.extend(["", "", "## Key Findings & Recommendations",
            "Based on the synthesized research above, this blueprint provides:",
            "- Product positioning and messaging",
            "- Target audience identification",
            "- Competitive differentiation",
            "- Go-to-market channels and tactics",
            "- Launch timeline and milestones",
            "",
            "## Next Steps",
            "1. Review and refine the research insights",
            "2. Validate assumptions with stakeholders",
            "3. Execute the launch plan with defined milestones",
            "4. Monitor and iterate based on performance data",
            "",
            "## Assumptions & Limitations",
            "- Research is based on available data sources",
            "- Some findings may require additional validation",
            "- Market conditions may change during launch period",
            ""])

        blueprint_content = chr(10).join(blueprint_lines)

        # Write blueprint.md
        blueprint_path = Path(f"/projects/{project_slug}/blueprint.md")
        blueprint_path.parent.mkdir(parents=True, exist_ok=True)
        blueprint_path.write_text(blueprint_content, encoding="utf-8")

        print(f"[progress] Blueprint created successfully at {blueprint_path}", file=output, flush=True)

    except Exception as e:
        print(f"[error] Failed to create blueprint.md: {e}", file=output, flush=True)


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
    
    # Build supervisor with dependency management and sequential execution
    supervisor = build_supervisor(settings)
    
    # Stream response and create blueprint after completion
    stream_response(
        supervisor,
        agent_input,
        {"callbacks": callbacks},
        sys.stdout,
    )
    
    # Create blueprint after supervisor completes
    _create_blueprint(supervisor, request.project_slug, sys.stdout)
    
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
