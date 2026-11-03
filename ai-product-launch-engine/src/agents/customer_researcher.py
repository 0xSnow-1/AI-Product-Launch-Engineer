"""Customer-research subagent registration."""

from __future__ import annotations

from pathlib import Path

import yaml

from agents.tools import search_tool


PROMPT_PATH = Path(__file__).resolve().parents[1] / "prompts" / "subagents" / "customer_researcher" / "v3.yaml"
SYSTEM_PROMPT = yaml.safe_load(PROMPT_PATH.read_text(encoding="utf-8"))["system_prompt"]

customer_researcher = {
    "name": "customer_researcher",
    "description": "Research customers, jobs, buying triggers, and assumptions. Write customer_research.json.",
    "tools": [search_tool],
    "system_prompt": SYSTEM_PROMPT,
}
