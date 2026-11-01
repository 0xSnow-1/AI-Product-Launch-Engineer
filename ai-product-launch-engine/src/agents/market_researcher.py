"""Market-research subagent registration."""

from __future__ import annotations

from typing import Any

from agents.common import load_prompt


def definition(model: Any, search_tool: Any) -> dict[str, Any]:
    """Return the declarative subagent used by the supervisor."""

    return {
        "name": "market_researcher",
        "description": "Research competitors, market opportunities, and cited evidence. Write market.md.",
        "model": model,
        "tools": [search_tool],
        "system_prompt": load_prompt("subagents", "market_researcher", "v2.yaml"),
    }
