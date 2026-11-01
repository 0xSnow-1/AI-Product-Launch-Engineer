"""Shared, lazy runtime helpers for launch agents."""

from __future__ import annotations

from pathlib import Path

import yaml

from src.config import Settings


PROMPTS_ROOT = Path(__file__).resolve().parents[1] / "prompts"


def load_prompt(*parts: str) -> str:
    """Load one versioned prompt and return its system prompt text."""

    prompt_path = PROMPTS_ROOT.joinpath(*parts)
    prompt_data = yaml.safe_load(prompt_path.read_text(encoding="utf-8"))
    system_prompt = prompt_data.get("system_prompt") if isinstance(prompt_data, dict) else None
    if not isinstance(system_prompt, str) or not system_prompt.strip():
        raise ValueError(f"Prompt has no system_prompt: {prompt_path}")
    return system_prompt


def create_model(settings: Settings):
    """Construct the Bedrock chat model without invoking it."""

    from langchain_aws import ChatBedrockConverse

    return ChatBedrockConverse(model=settings.bedrock_model_id, region_name=settings.bedrock_region)


def create_backend(settings: Settings):
    """Create the shared virtual filesystem backend at the canonical physical root."""

    from deepagents.backends import FilesystemBackend

    settings.workspace_root.mkdir(parents=True, exist_ok=True)
    return FilesystemBackend(root_dir=settings.workspace_root, virtual_mode=True)


def create_search_tool():
    """Create the research search tool without performing a search."""

    from langchain_tavily import TavilySearch

    return TavilySearch(max_results=5)
