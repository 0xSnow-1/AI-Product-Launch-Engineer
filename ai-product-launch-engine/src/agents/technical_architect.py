"""Technical architecture subagent.

Designs the MVP architecture, data model, APIs, and implementation plan.
"""

from pathlib import Path

import yaml

PROMPT_DIR = Path(__file__).resolve().parents[1] / "prompts" / "subagents" / "technical_architect" / "v1.yaml"

SYSTEM_PROMPT = yaml.safe_load(PROMPT_DIR.read_text(encoding="utf-8"))["system_prompt"]
