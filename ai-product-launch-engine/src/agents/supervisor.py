"""Supervisor agent for the AI Product Launch Engineer."""

from __future__ import annotations

from pathlib import Path
from typing import Any, TextIO

import boto3
import yaml
from botocore.client import Config
from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend
from dotenv import load_dotenv
from langchain.agents.middleware import TodoListMiddleware
from langchain_aws import ChatBedrockConverse

from agents.customer_researcher import customer_researcher
from agents.gtm_strategist import gtm_strategist
from agents.market_researcher import market_researcher
from agents.tools import search_tool
from src.config import Settings


load_dotenv()

PROMPT_PATH = Path(__file__).resolve().parents[1] / "prompts" / "supervisor" / "v2.yaml"
SYSTEM_PROMPT = yaml.safe_load(PROMPT_PATH.read_text(encoding="utf-8"))["system_prompt"]

settings = Settings.from_environment(project_root=Path(__file__).resolve().parents[2])
settings.workspace_root.mkdir(parents=True, exist_ok=True)

bedrock_runtime_client = boto3.client(
    "bedrock-runtime",
    region_name=settings.bedrock_region,
    config=Config(
        read_timeout=300,
        connect_timeout=60,
        retries={"max_attempts": 3},
    ),
)

model = ChatBedrockConverse(
    model=settings.bedrock_model_id,
    region_name=settings.bedrock_region,
    client=bedrock_runtime_client,
)

supervisor = create_deep_agent(
    model=model,
    backend=FilesystemBackend(root_dir=settings.workspace_root, virtual_mode=True),
    system_prompt=SYSTEM_PROMPT,
    tools=[search_tool],
    middleware=[TodoListMiddleware()],
    subagents=[market_researcher, customer_researcher, gtm_strategist],
    name="product_launch_supervisor",
)


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
    messages = agent_input.get("messages", [])
    if isinstance(messages, list) and messages:
        print(f"Project: {messages[0]['content']}", file=output, flush=True)


def create_blueprint(agent: Any, project_slug: str, output: TextIO) -> None:
    """Create the final blueprint.md artifact synthesizing market, customer, and GTM research."""

    print("[progress] Creating blueprint.md from research artifacts...", file=output, flush=True)

    try:
        market_path = Path(f"/projects/{project_slug}/research/market.md")
        customers_path = Path(f"/projects/{project_slug}/research/customers.md")
        gtm_path = Path(f"/projects/{project_slug}/strategy/gtm.md")

        artifacts = {}
        if market_path.exists():
            artifacts["market_research"] = market_path.read_text(encoding="utf-8")
        if customers_path.exists():
            artifacts["customer_research"] = customers_path.read_text(encoding="utf-8")
        if gtm_path.exists():
            artifacts["gtm_strategy"] = gtm_path.read_text(encoding="utf-8")

        market_content = artifacts.get("market_research", "")[:1000] if artifacts.get("market_research") else ""
        customer_content = artifacts.get("customer_research", "")[:1000] if artifacts.get("customer_research") else ""
        gtm_content = artifacts.get("gtm_strategy", "")[:1000] if artifacts.get("gtm_strategy") else ""

        blueprint_lines = [
            "# Product Launch Blueprint",
            "",
            f"## Project: {project_slug}",
            f"Generated: {Path.cwd()}",
            "",
            "## Executive Summary",
            "This blueprint synthesizes market research, customer insights, and go-to-market strategy to provide a comprehensive launch plan.",
            "",
            "## Market Research",
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

        blueprint_lines.extend([
            "",
            "",
            "## Key Findings & Recommendations",
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
            "",
        ])

        blueprint_content = "\n".join(blueprint_lines)

        blueprint_path = Path(f"/projects/{project_slug}/blueprint.md")
        blueprint_path.parent.mkdir(parents=True, exist_ok=True)
        blueprint_path.write_text(blueprint_content, encoding="utf-8")

        print(f"[progress] Blueprint created successfully at {blueprint_path}", file=output, flush=True)
    except Exception as error:
        print(f"[error] Failed to create blueprint.md: {error}", file=output, flush=True)
