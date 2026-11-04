"""Supervisor agent for the AI Product Launch Engineer."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable, TextIO

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
from src.workflows.validation import validate_project


load_dotenv()

PROMPT_PATH = Path(__file__).resolve().parents[1] / "prompts" / "supervisor" / "v4.yaml"
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


def create_blueprint(agent: Any, project_slug: str, workspace_root: Path, output: TextIO) -> None:
    """Create the final blueprint.md artifact synthesizing market, customer, and GTM research."""

    print("[progress] Creating blueprint.md from research artifacts...", file=output, flush=True)

    project_root = workspace_root / "projects" / project_slug
    artifacts = validate_project(project_root)
    market = artifacts["market_research"]
    customer = artifacts["customer_research"]
    gtm = artifacts["gtm_strategy"]

    def _bullets(items: Iterable[str]) -> list[str]:
        return [f"- {item}" for item in items] or ["- None recorded"]

    competitor_lines = [f"- {competitor.name}: {competitor.positioning}" for competitor in market.competitors] or ["- None recorded"]
    persona_lines = [f"- {persona.name} ({persona.role})" for persona in customer.personas] or ["- None recorded"]
    roadmap_lines = [f"- {phase.name} ({phase.timeline})" for phase in gtm.launch_roadmap] or ["- None recorded"]

    blueprint_lines = [
        "# Product Launch Blueprint",
        "",
        f"## Project: {project_slug}",
        "",
        "## Market Research",
        market.summary,
        "",
        "Competitors:",
        *competitor_lines,
        "",
        "Market opportunities:",
        *_bullets(market.market_opportunities),
        "",
        "Trends:",
        *_bullets(market.trends),
        "",
        "## Customer Research",
        f"Ideal customer profile: {customer.ideal_customer_profile}",
        "",
        "Personas:",
        *persona_lines,
        "",
        "Pain points:",
        *_bullets(customer.pain_points),
        "",
        "Buying triggers:",
        *_bullets(customer.buying_triggers),
        "",
        "## GTM Strategy",
        f"Positioning: {gtm.positioning}",
        "",
        f"Differentiation: {gtm.differentiation}",
        "",
        "Channels:",
        *_bullets(gtm.channels),
        "",
        "Launch roadmap:",
        *roadmap_lines,
        "",
        "## Risks and Assumptions",
    ]

    risk_lines: list[str] = []
    for assumption in [*market.assumptions, *customer.assumptions, *gtm.assumptions]:
        risk_lines.append(f"- Assumption: {assumption}")
    for risk in gtm.risks:
        risk_lines.append(f"- Risk: {risk}")
    for limitation in [*market.limitations, *customer.limitations]:
        risk_lines.append(f"- Limitation: {limitation}")
    blueprint_lines.extend(risk_lines or ["- None recorded"])
    blueprint_lines.append("")

    blueprint_content = "\n".join(blueprint_lines)

    blueprint_path = project_root / "blueprint.md"
    blueprint_path.parent.mkdir(parents=True, exist_ok=True)
    blueprint_path.write_text(blueprint_content, encoding="utf-8")

    print(f"[progress] Blueprint created successfully at {blueprint_path}", file=output, flush=True)
