"""ArchitectSession: one design project = one workspace folder + one Aider coder with persistent chat state."""
from __future__ import annotations

import json
import os
import re
import threading
from typing import Any, Dict, List, Optional

from aider.coders import Coder
from aider.models import Model

from .coder import DESIGN_FILE, EDIT_FORMAT, ArchitectureCoder, ensure_workspace
from .interface import ChatResult
from .io import RecordingIO
from .runner import run_workspace

_BLOCK = re.compile(r"(^|\n)[^\n]*\n```python\n<<<<<<< SEARCH.*?>>>>>>> REPLACE\n```", re.S)


def strip_edit_blocks(text: str) -> str:
    return re.sub(r"\n{3,}", "\n\n", _BLOCK.sub("\n", text or "")).strip()


class ArchitectSession:
    """Aider adapter: implements agent.interface.ArchitectureAgent on top of an Aider Coder."""

    def __init__(self, workspace: str, model: str = "gpt-4o", coder: Optional[ArchitectureCoder] = None,
                 io: Optional[RecordingIO] = None):
        self.workspace = os.path.abspath(workspace)
        self.design_path = ensure_workspace(self.workspace)
        self.io = io or RecordingIO()
        self._lock = threading.Lock()
        if coder is None:
            coder = Coder.create(
                main_model=Model(model), edit_format=EDIT_FORMAT, io=self.io, fnames=[self.design_path],
                use_git=False, map_tokens=0, stream=False, auto_commits=False, dirty_commits=False,
                suggest_shell_commands=False, detect_urls=False, auto_lint=False,
            )
        self.phase = "idle"
        self.coder: ArchitectureCoder = coder.configure(self.workspace, on_phase=self._set_phase)
        self.io = self.coder.io

    def _set_phase(self, name: str):
        self.phase = name

    # ------------------------------------------------------------------ chat
    def chat(self, message: str) -> ChatResult:
        with self._lock:
            self.io.drain()
            self.phase = "understanding"
            try:
                self.coder.run(with_message=message, preproc=False)
            except Exception:
                self.phase = "failed"
                raise
            events = self.io.drain()
            replies = [strip_edit_blocks(e["text"]) for e in events if e["kind"] == "assistant"]
            replies = [r for r in replies if r]
            status = self.coder.last_status or self.read_status()
            errs = (status.get("report") or {}).get("errors") or []
            self.phase = "failed" if (self.coder.last_rolled_back or (errs and not status.get("valid"))) else ("ready" if status.get("valid") else "idle")
            return ChatResult(reply="\n\n".join(replies[-1:]) if replies else "", valid=bool(status.get("valid")),
                              rolled_back=self.coder.last_rolled_back, status=status, events=events,
                              rejected=(self.coder.rejected_status or {}).get("report") if self.coder.last_rolled_back else None)

    # ------------------------------------------------------------------ state for the UI
    def read_status(self) -> Dict[str, Any]:
        p = os.path.join(self.workspace, "out", "status.json")
        if os.path.exists(p):
            with open(p, encoding="utf-8") as fh:
                return json.load(fh)
        return {"valid": False, "report": {"valid": False, "errors": [], "warnings": []}, "artifacts": {}, "stale": True}

    def rebuild(self) -> Dict[str, Any]:
        ok, text, status = run_workspace(self.workspace, DESIGN_FILE)
        self.coder.last_status = status
        return status

    def state(self) -> Dict[str, Any]:
        model = None
        mp = os.path.join(self.workspace, "out", "model.json")
        if os.path.exists(mp):
            with open(mp, encoding="utf-8") as fh:
                model = json.load(fh)
        with open(self.design_path, encoding="utf-8") as fh:
            design = fh.read()
        return {"design": design, "model": model, "status": self.read_status()}
