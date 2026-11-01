"""Go-to-market strategy subagent registration."""

from __future__ import annotations

from typing import Any

from agents.common import load_prompt


def definition(model: Any, search_tool: Any) -> dict[str, Any]:
    """Return the declarative subagent used by the supervisor."""

    return {
        "name": "gtm_strategist",
        "description": "Create positioning, messaging, and distribution strategy. Write gtm.md.",
        "model": model,
        "tools": [search_tool],
        "system_prompt": load_prompt("subagents", "gtm_strategist", "v2.yaml"),
    }
