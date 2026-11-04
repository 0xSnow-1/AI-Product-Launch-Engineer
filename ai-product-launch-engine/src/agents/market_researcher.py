"""Market-research subagent registration."""

from __future__ import annotations

from pathlib import Path

import yaml

from agents.tools import search_tool


PROMPT_PATH = Path(__file__).resolve().parents[1] / "prompts" / "subagents" / "market_researcher" / "v3.yaml"
SYSTEM_PROMPT = yaml.safe_load(PROMPT_PATH.read_text(encoding="utf-8"))["system_prompt"]

market_researcher = {
    "name": "market_researcher",
    "description": "Research competitors, market opportunities, and cited evidence. Write market_research.json.",
    "tools": [search_tool],
    "system_prompt": SYSTEM_PROMPT,
}
