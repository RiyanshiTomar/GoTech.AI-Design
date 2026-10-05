"""Aider InputOutput that never blocks (auto-confirm) and records events for the UI."""
from __future__ import annotations

from typing import Any, Dict, List

from aider.io import InputOutput


class RecordingIO(InputOutput):
    def __init__(self, **kw):
        kw.setdefault("yes", True)
        kw.setdefault("pretty", False)
        kw.setdefault("fancy_input", False)
        kw.setdefault("input_history_file", None)
        kw.setdefault("chat_history_file", None)
        super().__init__(**kw)
        self.events: List[Dict[str, Any]] = []

    def _rec(self, kind, text):
        if text:
            self.events.append({"kind": kind, "text": str(text)})

    def tool_output(self, *messages, log_only=False, bold=False):
        self._rec("info", " ".join(str(m) for m in messages))
        super().tool_output(*messages, log_only=log_only, bold=bold)

    def tool_warning(self, message="", strip=True):
        self._rec("warning", message)
        super().tool_warning(message, strip=strip)

    def tool_error(self, message="", strip=True):
        self._rec("error", message)
        super().tool_error(message, strip=strip)

    def ai_output(self, content):
        self._rec("assistant", content)

    def drain(self) -> List[Dict[str, Any]]:
        ev, self.events = self.events, []
        return ev
