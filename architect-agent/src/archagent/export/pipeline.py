"""validate -> (only if valid) SVG + IFC + GLB. Invalid models are never rendered as if correct."""
from __future__ import annotations

import json
import os
import time
import traceback
from typing import Any, Dict

from ..validation import validate_building
from .glb import export_glb
from .ifc import export_ifc
from .svg import render_all_svgs

ARTIFACT_DIRNAME = "artifacts"


def build_artifacts(model: Dict[str, Any], out_dir: str, on_phase=None) -> Dict[str, Any]:
    """Writes model.json + status.json always. Writes svg/ifc/glb only when validation passes.

    Previous valid artifacts are kept on failure but flagged ``stale`` in status.json so the UI can say so.
    """
    os.makedirs(out_dir, exist_ok=True)
    art_dir = os.path.join(out_dir, ARTIFACT_DIRNAME)
    os.makedirs(art_dir, exist_ok=True)
    with open(os.path.join(out_dir, "model.json"), "w", encoding="utf-8") as fh:
        json.dump(model, fh, indent=2)

    report = validate_building(model)
    status: Dict[str, Any] = {"valid": report.valid, "report": report.to_dict(), "artifacts": {}, "stale": not report.valid,
                              "built_at": time.time(), "export_errors": []}
    if report.valid:
        if on_phase:
            on_phase("rendering")
        steps = (
            ("svg", lambda: [os.path.relpath(p, out_dir) for p in render_all_svgs(model, art_dir)]),
            ("ifc", lambda: os.path.relpath(export_ifc(model, os.path.join(art_dir, "building.ifc")), out_dir)),
            ("glb", lambda: os.path.relpath(export_glb(model, os.path.join(art_dir, "building.glb")), out_dir)),
        )
        for name, fn in steps:
            try:
                status["artifacts"][name] = fn()
            except Exception as e:
                status["export_errors"].append({"code": f"{name.upper()}_EXPORT_FAILED", "objects": [name],
                                                "details": f"{type(e).__name__}: {e}",
                                                "trace": traceback.format_exc(limit=4)})
        if status["export_errors"]:
            status["valid"] = False
            status["stale"] = True
    else:
        prev = os.path.join(out_dir, "status.json")
        if os.path.exists(prev):
            try:
                with open(prev, encoding="utf-8") as fh:
                    status["artifacts"] = json.load(fh).get("artifacts", {})
            except Exception:
                pass
    with open(os.path.join(out_dir, "status.json"), "w", encoding="utf-8") as fh:
        json.dump(status, fh, indent=2)
    status["_report"] = report
    return status
