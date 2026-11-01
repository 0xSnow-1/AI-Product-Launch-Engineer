"""Customer-research subagent registration."""

from __future__ import annotations

from typing import Any

from agents.common import load_prompt


def definition(model: Any, search_tool: Any) -> dict[str, Any]:
    """Return the declarative subagent used by the supervisor."""

    return {
        "name": "customer_researcher",
        "description": "Research customers, jobs, buying triggers, and assumptions. Write customers.md.",
        "model": model,
        "tools": [search_tool],
        "system_prompt": load_prompt("subagents", "customer_researcher", "v2.yaml"),
    }
