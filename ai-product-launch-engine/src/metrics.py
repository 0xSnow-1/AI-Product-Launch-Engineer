"""Runtime metrics collected from the JSON Lines agent transcript."""

from __future__ import annotations

import ast
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping


DELEGATION_EVENTS = frozenset({"delegation_started", "delegation_finished"})


def _transcript_path_from_environment() -> Path | None:
    """Return the configured transcript path, or None when it is absent."""

    raw = os.environ.get("LAUNCH_ENGINE_TRANSCRIPT_PATH")
    if not raw or not raw.strip():
        return None
    return Path(raw.strip())


def _parse_timestamp(value: Any) -> datetime | None:
    """Parse an ISO 8601 timestamp."""

    if not isinstance(value, str) or not value.strip():
        return None
    try:
        return datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        return None


def _parse_tool_input(value: Any) -> Mapping[str, Any] | None:
    """Accept JSON input and Python dict string input."""

    if isinstance(value, Mapping):
        return value
    if not isinstance(value, str):
        return None
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        try:
            parsed = ast.literal_eval(value)
        except (ValueError, SyntaxError):
            return None
    return parsed if isinstance(parsed, Mapping) else None


def _event_subagent(event: Mapping[str, Any]) -> str | None:
    """Return the subagent name when the event is a delegation event."""

    subagent = event.get("subagent")
    if isinstance(subagent, str) and subagent.strip():
        return subagent.strip()
    if event.get("event") not in DELEGATION_EVENTS and event.get("tool") != "task":
        return None
    input_data = _parse_tool_input(event.get("input"))
    if input_data is None:
        return None
    candidate = input_data.get("subagent_type")
    if isinstance(candidate, str) and candidate.strip():
        return candidate.strip()
    return None


def _token_count(event: Mapping[str, Any]) -> int | None:
    """Return one token total from a model event, or None when absent."""

    for key in ("total_tokens", "tokens"):
        value = event.get(key)
        if isinstance(value, int) and not isinstance(value, bool):
            return value
    usage = event.get("usage")
    if isinstance(usage, Mapping):
        value = usage.get("total_tokens")
        if isinstance(value, int) and not isinstance(value, bool):
            return value
        input_tokens = usage.get("input_tokens")
        output_tokens = usage.get("output_tokens")
        if (
            isinstance(input_tokens, int)
            and not isinstance(input_tokens, bool)
            and isinstance(output_tokens, int)
            and not isinstance(output_tokens, bool)
        ):
            return input_tokens + output_tokens
    return None


def collect_metrics(transcript_path: Path | None = None) -> dict[str, Any]:
    """Read one transcript and return the runtime metrics for a trial.

    Missing transcripts and missing values return zeros.
    """

    path = Path(transcript_path) if transcript_path is not None else _transcript_path_from_environment()
    metrics: dict[str, Any] = {
        "agents_used": [],
        "total_turns": 0,
        "total_tool_calls": 0,
        "total_tokens": 0,
    }
    if path is None or not path.is_file():
        return metrics

    agents: list[str] = []
    agents_seen: set[str] = set()
    turns = 0
    tool_calls = 0
    tokens = 0
    tokens_seen = False

    events_seen = False
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(event, Mapping):
            continue
        events_seen = True
        event_type = event.get("event")
        if event_type == "model_started":
            turns += 1
        elif event_type == "tool_started":
            tool_calls += 1
        subagent = _event_subagent(event)
        if subagent is not None and subagent not in agents_seen:
            agents_seen.add(subagent)
            agents.append(subagent)
        token_count = _token_count(event)
        if token_count is not None:
            tokens += token_count
            tokens_seen = True

    metrics["agents_used"] = (["supervisor", *agents] if events_seen else agents)
    metrics["total_turns"] = turns
    metrics["total_tool_calls"] = tool_calls
    metrics["total_tokens"] = tokens if tokens_seen else 0
    return metrics
