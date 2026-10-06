"""ArchitectureCoder: Aider's edit-block coder, re-purposed to edit design.py and validate after every edit.

What is reused from Aider unchanged: chat history, SEARCH/REPLACE parsing and applying, the reflection loop
(`reflected_message`), litellm model access, retry/backoff.
What changes: prompts (architecture persona + knowledge), `test_cmd` is the deterministic build/validate runner
(its failure text is fed back to the LLM), more reflections, and rollback so invalid geometry never stays as the
current design.
"""
from __future__ import annotations

import json
import os
import shutil
from typing import Any, Dict, Optional

import aider.coders as _aider_coders
from aider.coders.editblock_coder import EditBlockCoder

from .prompts import ArchitectPrompts, STARTER_DESIGN
from .runner import run_workspace

EDIT_FORMAT = "architect-design"
DESIGN_FILE = "design.py"
MAX_REPAIR_ROUNDS = 6


class ArchitectureCoder(EditBlockCoder):
    edit_format = EDIT_FORMAT
    gpt_prompts = ArchitectPrompts()

    workspace: str = "."
    last_status: Optional[Dict[str, Any]] = None
    last_rolled_back: bool = False
    rejected_status: Optional[Dict[str, Any]] = None

    # -- wiring --------------------------------------------------------------------------------------
    def configure(self, workspace: str, on_phase=None):
        self.workspace = os.path.abspath(workspace)
        self._on_phase = on_phase
        self.auto_lint = False
        self.auto_test = True
        self.test_cmd = self._validate_cmd
        self.max_reflections = MAX_REPAIR_ROUNDS
        self.suggest_shell_commands = False
        self.detect_urls = False
        return self

    _on_phase = None

    def set_phase(self, name: str):
        if self._on_phase:
            self._on_phase(name)

    def send_message(self, inp):
        self.set_phase("repairing" if self.num_reflections > 0 else "generating")
        yield from super().send_message(inp)

    @property
    def design_path(self) -> str:
        return os.path.join(self.workspace, DESIGN_FILE)

    def _validate_cmd(self) -> Optional[str]:
        """Aider's test hook: return error text for the LLM, or None when everything passed."""
        ok, text, status = run_workspace(self.workspace, DESIGN_FILE, on_phase=self.set_phase)
        self.last_status = status
        return None if ok else text

    def get_platform_info(self):
        # Aider concatenates test_cmd into this text; ours is a callable and OS details are irrelevant here.
        return ""

    # -- one user turn ---------------------------------------------------------------------------------
    def state_hint(self) -> str:
        st = self.last_status
        if st is None:
            return "Current validation status: not run yet."
        if st.get("valid"):
            return "Current validation status: VALID (design.py is the current building)."
        codes = sorted({e["code"] for e in st.get("report", {}).get("errors", [])})
        return f"Current validation status: INVALID ({', '.join(codes)})."

    def run_one(self, user_message, preproc):
        before = self._read_design()
        self.last_rolled_back = False
        self.rejected_status = None
        message = f"{user_message}\n\n[{self.state_hint()}]"
        self.set_phase("understanding")
        super().run_one(message, preproc)
        # Final authority: re-run the deterministic pipeline on whatever design.py is now.
        after = self._read_design()
        if after != before:
            ok, text, status = run_workspace(self.workspace, DESIGN_FILE, on_phase=self.set_phase)
            self.last_status = status
            if not ok:
                self._write_design(before)
                self.last_rolled_back = True
                self.io.tool_warning("The final design did not pass validation, so the previous valid design was restored.")
                self.io.tool_output(text)
                self.rejected_status = status
                self.last_status = run_workspace(self.workspace, DESIGN_FILE)[2]   # status of the restored design
                # tell the model so the next turn starts from the truth
                self.set_phase("failed")
                self.done_messages += [
                    dict(role="user", content="SYSTEM: your last design failed validation and was rolled back to the previous valid version."),
                    dict(role="assistant", content="Understood. The previous valid design is current."),
                ]

    def _read_design(self) -> str:
        try:
            with open(self.design_path, encoding="utf-8") as fh:
                return fh.read()
        except OSError:
            return ""

    def _write_design(self, text: str):
        with open(self.design_path, "w", encoding="utf-8") as fh:
            fh.write(text)


def register():
    """Make Coder.create(edit_format='architect-design') find our class."""
    if ArchitectureCoder not in _aider_coders.__all__:
        _aider_coders.__all__.append(ArchitectureCoder)


register()


def ensure_workspace(workspace: str) -> str:
    os.makedirs(os.path.join(workspace, "out"), exist_ok=True)
    path = os.path.join(workspace, DESIGN_FILE)
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(STARTER_DESIGN)
    return path
