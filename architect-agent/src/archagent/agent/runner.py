"""Executes design.py (the LLM-authored program) and runs the pipeline.

Usage: python -m archagent.agent.runner <workspace_dir> [design.py]
Exit code 0 only when the design is valid and every artifact was produced.
Failure prints structured, agent-readable errors (this is what Aider feeds back to the LLM).
"""
from __future__ import annotations

import io
import json
import os
import sys
import traceback
from contextlib import redirect_stdout
from typing import Any, Dict, Optional, Tuple

from ..core import Building
from ..export.pipeline import build_artifacts
from .sandbox import run_design_file
from ..validation.issues import Issue, ValidationReport, error

MAX_DESIGN_BYTES = 400_000


def run_design(path: str) -> Tuple[Optional[Building], Optional[Issue]]:
    """Run design.py in the sandbox. Never raises; returns (building, python_error)."""
    try:
        size = os.path.getsize(path)
    except OSError as e:
        return None, error("DESIGN_MISSING", [path], f"Cannot read design file: {e}")
    if size == 0 or not open(path, encoding="utf-8").read().strip():
        return None, error("DESIGN_EMPTY", [path], "design.py is empty. It must create a Building and assign it to `building`.")
    if size > MAX_DESIGN_BYTES:
        return None, error("DESIGN_TOO_LARGE", [path], "design.py is unreasonably large.")
    model, err = run_design_file(path)
    if err is not None:
        return None, error(err["code"], [err.get("where", path)], err["details"], hint=err.get("hint"))
    try:
        return Building.from_dict(model), None
    except ValueError as e:
        return None, error("MALFORMED_MODEL", ["model"], str(e))


def run_workspace(workspace: str, design: str = "design.py", on_phase=None) -> Tuple[bool, str, Dict[str, Any]]:
    """Returns (ok, text_for_agent, status_dict)."""
    out_dir = os.path.join(workspace, "out")
    os.makedirs(out_dir, exist_ok=True)
    if on_phase:
        on_phase("validating")
    b, py_err = run_design(os.path.join(workspace, design))
    if py_err is not None:
        report = ValidationReport()
        report.add(py_err)
        status = {"valid": False, "report": report.to_dict(), "artifacts": {}, "stale": True, "export_errors": []}
        try:
            prev = json.load(open(os.path.join(out_dir, "status.json"), encoding="utf-8"))
            status["artifacts"] = prev.get("artifacts", {})
        except Exception:
            pass
        with open(os.path.join(out_dir, "status.json"), "w", encoding="utf-8") as fh:
            json.dump(status, fh, indent=2)
        return False, report.format_for_agent(), status
    status = build_artifacts(b.to_dict(), out_dir, on_phase=on_phase)
    report: ValidationReport = status.pop("_report")
    if not report.valid:
        return False, report.format_for_agent(), status
    if status["export_errors"]:
        return False, "EXPORT FAILED:\n" + json.dumps(status["export_errors"], indent=2), status
    _snapshot_last_valid(workspace, design, out_dir)
    if on_phase:
        on_phase("ready")
    return True, report.format_for_agent() + "\nAll artifacts (SVG per floor, IFC, GLB) were generated.", status


def _snapshot_last_valid(workspace: str, design: str, out_dir: str) -> None:
    """Persist the last design that passed validation, independent of chat history."""
    import shutil
    d = os.path.join(workspace, "last_valid")
    os.makedirs(d, exist_ok=True)
    shutil.copyfile(os.path.join(workspace, design), os.path.join(d, "design.py"))
    shutil.copyfile(os.path.join(out_dir, "model.json"), os.path.join(d, "model.json"))


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv:
        print("usage: python -m archagent.agent.runner <workspace> [design.py]")
        return 2
    ok, text, _ = run_workspace(argv[0], argv[1] if len(argv) > 1 else "design.py")
    print(text)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
