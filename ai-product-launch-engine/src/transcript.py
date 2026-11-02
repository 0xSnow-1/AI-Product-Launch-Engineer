"""JSON Lines transcript recording for real agent invocations."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping


def _serialize(value: Any) -> str:
    return json.dumps(value, default=str, sort_keys=True)


def _identifier(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def _model_name(serialized: Any, metadata: Any) -> str | None:
    if isinstance(serialized, Mapping):
        name = serialized.get("name")
        if isinstance(name, str) and name:
            return name
        kwargs = serialized.get("kwargs")
        if isinstance(kwargs, Mapping):
            for key in ("model", "model_id", "model_name"):
                value = kwargs.get(key)
                if isinstance(value, str) and value:
                    return value
    if isinstance(metadata, Mapping):
        for key in ("ls_model_name", "model", "model_id", "model_name"):
            value = metadata.get(key)
            if isinstance(value, str) and value:
                return value
    return None


class JsonlCallbackHandler:
    """Create a LangChain callback handler only when a transcript path is configured."""

    def __new__(cls, transcript_path: Path):
        from langchain_core.callbacks import BaseCallbackHandler

        class Handler(BaseCallbackHandler):
            def __init__(self) -> None:
                self._tool_names: dict[str, str | None] = {}
                self._model_names: dict[str, str | None] = {}

            def _write(self, event: str, payload: dict[str, Any]) -> None:
                transcript_path.parent.mkdir(parents=True, exist_ok=True)
                record = {"event": event, "timestamp": datetime.now(UTC).isoformat(), **payload}
                with transcript_path.open("a", encoding="utf-8") as transcript:
                    transcript.write(f"{_serialize(record)}\n")

            @staticmethod
            def _context(
                run_id: Any,
                parent_run_id: Any,
                tags: Any,
                metadata: Any,
            ) -> dict[str, Any]:
                return {
                    "run_id": _identifier(run_id),
                    "parent_run_id": _identifier(parent_run_id),
                    "tags": list(tags) if tags else None,
                    "metadata": dict(metadata) if metadata else None,
                }

            def on_chat_model_start(
                self,
                serialized: dict[str, Any],
                messages: list[Any],
                run_id: Any = None,
                parent_run_id: Any = None,
                tags: Any = None,
                metadata: Any = None,
                **kwargs: Any,
            ) -> None:
                key = _identifier(run_id)
                name = _model_name(serialized, metadata)
                if key is not None:
                    self._model_names[key] = name
                self._write(
                    "model_started",
                    {**self._context(run_id, parent_run_id, tags, metadata), "model": name, "messages": messages},
                )

            def on_llm_end(
                self,
                response: Any,
                run_id: Any = None,
                parent_run_id: Any = None,
                tags: Any = None,
                metadata: Any = None,
                **kwargs: Any,
            ) -> None:
                key = _identifier(run_id)
                name = self._model_names.pop(key, None) if key is not None else None
                self._write(
                    "model_finished",
                    {**self._context(run_id, parent_run_id, tags, metadata), "model": name, "response": response},
                )

            def on_llm_error(
                self,
                error: BaseException,
                run_id: Any = None,
                parent_run_id: Any = None,
                tags: Any = None,
                metadata: Any = None,
                **kwargs: Any,
            ) -> None:
                key = _identifier(run_id)
                name = self._model_names.pop(key, None) if key is not None else None
                self._write(
                    "model_failed",
                    {**self._context(run_id, parent_run_id, tags, metadata), "model": name, "error": str(error)},
                )

            def on_tool_start(
                self,
                serialized: dict[str, Any],
                input_str: str,
                run_id: Any = None,
                parent_run_id: Any = None,
                tags: Any = None,
                metadata: Any = None,
                **kwargs: Any,
            ) -> None:
                name = serialized.get("name") if isinstance(serialized, Mapping) else None
                key = _identifier(run_id)
                if key is not None:
                    self._tool_names[key] = name
                self._write(
                    "tool_started",
                    {**self._context(run_id, parent_run_id, tags, metadata), "tool": name, "input": input_str},
                )

            def on_tool_end(
                self,
                output: Any,
                run_id: Any = None,
                parent_run_id: Any = None,
                tags: Any = None,
                metadata: Any = None,
                **kwargs: Any,
            ) -> None:
                key = _identifier(run_id)
                name = self._tool_names.pop(key, None) if key is not None else None
                self._write(
                    "tool_finished",
                    {**self._context(run_id, parent_run_id, tags, metadata), "tool": name, "output": output},
                )

            def on_tool_error(
                self,
                error: BaseException,
                run_id: Any = None,
                parent_run_id: Any = None,
                tags: Any = None,
                metadata: Any = None,
                **kwargs: Any,
            ) -> None:
                key = _identifier(run_id)
                name = self._tool_names.pop(key, None) if key is not None else None
                self._write(
                    "tool_failed",
                    {**self._context(run_id, parent_run_id, tags, metadata), "tool": name, "error": str(error)},
                )

        return Handler()
