"""Design heuristics -> warnings only (never make a design invalid)."""
from __future__ import annotations

from ..geometry.common import room_has_geometry
from . import rules
from .issues import warning


def design_warnings(an):
    out = []
    for fg in an.floors:
        fl = fg.floor
        walls = {w.id: w for w in fg.walls}
        windowed = {op.room for op in fg.openings if op.kind == "window" and not op.problems}
        connects = {}
        for op in fg.openings:
            if op.kind == "door" and not op.problems:
                connects.setdefault(op.room, set()).add(op.connects)
                if op.connects:
                    connects.setdefault(op.connects, set()).add(op.room)
        for r in fg.rooms.values():
            if not room_has_geometry(r) or r.is_open:
                continue
            if r.kind in rules.HABITABLE and r.id not in windowed:
                out.append(warning("NO_DAYLIGHT", [r.name], f"{r.name} ({fl.name}) has no window; habitable rooms should get daylight and ventilation."))
            ar = max(r.width, r.depth) / min(r.width, r.depth)
            if r.kind in ("bedroom", "living", "dining", "kitchen") and ar > 2.2:
                out.append(warning("ROOM_PROPORTION", [r.name], f"{r.name} is {r.width:g} x {r.depth:g} m (aspect {ar:.1f}:1); a more compact shape is easier to furnish."))
            if r.kind == "kitchen":
                ids = connects.get(r.id, set())
                near = [fg.rooms[i].kind for i in ids if i in fg.rooms]
                if ids and not ({"dining", "living"} & set(near)):
                    out.append(warning("KITCHEN_ADJACENCY", [r.name], f"{r.name} does not open directly to the dining or living area."))
            if r.kind == "bathroom" and r.id not in connects:
                out.append(warning("BATHROOM_ACCESS", [r.name], f"{r.name} has no door."))
    return out
