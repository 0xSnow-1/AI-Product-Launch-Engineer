"""JSON Lines transcript recording for real agent invocations."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def _serialize(value: Any) -> str:
    return json.dumps(value, default=str, sort_keys=True)


class JsonlCallbackHandler:
    """Create a LangChain callback handler only when a transcript path is configured."""

    def __new__(cls, transcript_path: Path):
        from langchain_core.callbacks import BaseCallbackHandler

        class Handler(BaseCallbackHandler):
            def _write(self, event: str, payload: dict[str, Any]) -> None:
                transcript_path.parent.mkdir(parents=True, exist_ok=True)
                record = {"event": event, "timestamp": datetime.now(UTC).isoformat(), **payload}
                with transcript_path.open("a", encoding="utf-8") as transcript:
                    transcript.write(f"{_serialize(record)}\n")

            def on_chat_model_start(self, serialized: dict[str, Any], messages: list[Any], **kwargs: Any) -> None:
                self._write("model_started", {"model": serialized.get("name"), "messages": messages})

            def on_llm_end(self, response: Any, **kwargs: Any) -> None:
                self._write("model_finished", {"response": response})

            def on_llm_error(self, error: BaseException, **kwargs: Any) -> None:
                self._write("model_failed", {"error": str(error)})

            def on_tool_start(self, serialized: dict[str, Any], input_str: str, **kwargs: Any) -> None:
                self._write("tool_started", {"tool": serialized.get("name"), "input": input_str})

            def on_tool_end(self, output: Any, **kwargs: Any) -> None:
                self._write("tool_finished", {"output": output})

            def on_tool_error(self, error: BaseException, **kwargs: Any) -> None:
                self._write("tool_failed", {"error": str(error)})

        return Handler()
