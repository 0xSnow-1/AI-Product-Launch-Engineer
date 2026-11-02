"""Go-to-market strategy subagent registration."""

from __future__ import annotations

from pathlib import Path

import yaml


PROMPT_PATH = Path(__file__).resolve().parents[1] / "prompts" / "subagents" / "gtm_strategist" / "v2.yaml"
SYSTEM_PROMPT = yaml.safe_load(PROMPT_PATH.read_text(encoding="utf-8"))["system_prompt"]

gtm_strategist = {
    "name": "gtm_strategist",
    "description": "Create positioning, messaging, and distribution strategy. Write gtm.md.",
    "tools": [],
    "system_prompt": SYSTEM_PROMPT,
}
