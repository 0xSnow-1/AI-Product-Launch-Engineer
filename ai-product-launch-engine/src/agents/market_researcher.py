"""Market research subagent.

Researches competitors, market opportunities, and supporting evidence.
"""

from pathlib import Path

import yaml

PROMPT_DIR = Path(__file__).resolve().parents[1] / "prompts" / "subagents" / "market_researcher" / "v1.yaml"

SYSTEM_PROMPT = yaml.safe_load(PROMPT_DIR.read_text(encoding="utf-8"))["system_prompt"]
