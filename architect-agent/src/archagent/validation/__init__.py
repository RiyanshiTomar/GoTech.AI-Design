"""Deterministic geometric authority. The LLM never decides whether geometry is valid; this does."""
from __future__ import annotations

import traceback

from ..geometry import analyze
from .circulation import validate_circulation
from .floors import validate_floor_support
from .heuristics import design_warnings
from .issues import Issue, ValidationReport, error  # noqa: F401
from .openings import validate_openings
from .program import validate_program
from .rooms import validate_bounds, validate_overlaps, validate_room_dimensions
from .stairs import validate_stairs
from .structure import validate_duplicate_ids, validate_floors, validate_site, validate_units
from .walls import validate_walls

# Order matters only for readability of the report.
HARD_RULES = (
    validate_units, validate_site, validate_floors, validate_duplicate_ids, validate_room_dimensions,
    validate_bounds, validate_overlaps, validate_walls, validate_openings, validate_stairs,
    validate_floor_support, validate_circulation, validate_program,
)


def _resolve_ids(an, issue):
    """Map the human labels in issue.objects to persistent ids (room / door / window / stair / wall)."""
    import re
    by_label = {}
    all_ids = set()
    multi = len(an.building.floors) > 1
    for fg in an.floors:
        fl = fg.floor
        for r in fl.rooms:
            by_label[r.name] = r.id
            by_label[f"{r.name} ({fl.name})"] = r.id
            all_ids.add(r.id)
        for coll in (fl.doors, fl.windows, fl.stairs):
            all_ids.update(x.id for x in coll)
        all_ids.update(w.id for w in fg.walls)
    ids = []
    for o in issue.objects:
        found = by_label.get(o) or (o if o in all_ids else None)
        if not found:
            m = re.search(r"'([^']+)'", o)
            found = m.group(1) if m and m.group(1) in all_ids else None
        if found and found not in ids:
            ids.append(found)
    issue.object_ids = ids


def validate_building(model) -> ValidationReport:
    """model: Building or its dict. Never raises; internal failures become VALIDATOR_ERROR."""
    report = ValidationReport()
    try:
        an = analyze(model)
    except ValueError as e:
        report.add(error("MALFORMED_MODEL", ["model"], str(e)))
        return report
    except Exception as e:  # pragma: no cover - defensive
        report.add(error("VALIDATOR_ERROR", ["analysis"], f"{type(e).__name__}: {e}"))
        return report
    for rule in HARD_RULES:
        try:
            report.extend(rule(an))
        except Exception as e:  # a crashing rule must fail closed, never pass silently
            report.add(error("VALIDATOR_ERROR", [rule.__name__], f"{type(e).__name__}: {e}\n{traceback.format_exc(limit=3)}"))
    try:
        report.extend(design_warnings(an))
    except Exception:
        pass
    for issue in report.errors + report.warnings:
        try:
            _resolve_ids(an, issue)
        except Exception:
            pass
    b = an.building
    report.summary = {
        "floors": len(b.floors),
        "rooms": sum(len(f.rooms) for f in b.floors),
        "doors": sum(len(f.doors) for f in b.floors),
        "windows": sum(len(f.windows) for f in b.floors),
        "stairs": sum(len(f.stairs) for f in b.floors),
    }
    return report
