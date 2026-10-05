"""Stair geometry and floor-to-floor stair connection."""
from __future__ import annotations

from shapely.geometry import box
from shapely.ops import unary_union

from ..geometry.common import finite, room_has_geometry
from .issues import error, warning
from .rooms import allowed_region


def _enclosed_union(fg):
    boxes = [b for rid, b in fg.boxes.items() if not fg.rooms[rid].is_open]
    return unary_union(boxes) if boxes else None


def containing_room(fg, rect, enclosed_only=True):
    """Room whose box fully contains rect (or None)."""
    r = box(*rect)
    for rid, b in fg.boxes.items():
        if enclosed_only and fg.rooms[rid].is_open:
            continue
        if b.buffer(1e-6).contains(r):
            return fg.rooms[rid]
    return None


def validate_stairs(an):
    out = []
    allowed = allowed_region(an)
    floors = an.floors
    for i, fg in enumerate(floors):
        fl = fg.floor
        stair_boxes = []
        for st in fl.stairs:
            g = fg.stairs[st.id]
            tag = f"stair '{st.id}' ({fl.name})"
            for p in g.problems:
                code = "STAIR_TOO_SHORT" if "run" in p else "STAIR_TOO_NARROW" if "width" in p else "INVALID_VALUE"
                out.append(error(code, [tag], f"{tag} {p}.", hint="Increase the stair footprint, use shape='u' for a compact stair, or reduce floor height."))
            if g.footprint is None or not g.ok:
                continue
            fp = box(*g.footprint)
            stair_boxes.append((st, fp))
            if allowed is not None and not allowed.buffer(1e-6).contains(fp):
                out.append(error("STAIR_OUT_OF_BOUNDS", [tag], f"{tag} sticks out of the buildable area.", hint="Move the stair inside the building."))
                continue
            host = containing_room(fg, g.footprint)
            if host is None:
                out.append(error("STAIR_NOT_IN_ROOM", [tag], f"{tag} must lie completely inside one enclosed room (e.g. a staircase hall or the living room) on {fl.name}.",
                                 hint="Add a room of kind 'stair' around it or move the stair inside an existing room."))
                continue
            if g.entry_rect and not (allowed is not None and not allowed.buffer(1e-6).contains(box(*g.entry_rect))):
                if containing_room(fg, g.entry_rect) is None:
                    out.append(warning("STAIR_ENTRY_TIGHT", [tag], f"No clear approach space below the first step of {tag}; consider moving it within its room."))
            # connection upward
            if i + 1 >= len(floors):
                out.append(error("STAIR_NO_UPPER_FLOOR", [tag], f"{tag} leads nowhere: there is no floor above {fl.name}.",
                                 hint="Remove the stair or add an upper floor."))
                continue
            up = floors[i + 1]
            if containing_room(up, g.footprint) is None:
                out.append(error("STAIR_NO_LANDING_ABOVE", [tag], f"{up.floor.name} has no enclosed room around the stairwell of {tag}.",
                                 hint="Add a room (e.g. 'Landing' or 'Hall') on the upper floor covering the stair footprint."))
                continue
            if g.exit_rect:
                ex = box(*g.exit_rect)
                up_union = _enclosed_union(up)
                blocked = any(ex.intersects(box(*up.stairs[s.id].footprint)) and ex.intersection(box(*up.stairs[s.id].footprint)).area > 1e-4
                              for s in up.floor.stairs if up.stairs[s.id].footprint)
                if up_union is None or not up_union.buffer(1e-6).contains(ex) or blocked:
                    out.append(error("STAIR_NO_LANDING_ABOVE", [tag],
                                     f"There is no clear 1 m landing on {up.floor.name} where {tag} arrives (area x {g.exit_rect[0]:.2f}-{g.exit_rect[2]:.2f}, y {g.exit_rect[1]:.2f}-{g.exit_rect[3]:.2f} m must be inside upper rooms).",
                                     hint="Make the upper-floor room cover that landing area, or rotate the stair (direction=...)."))
        for (sa, pa), (sb, pb) in __import__("itertools").combinations(stair_boxes, 2):
            if pa.intersection(pb).area > 1e-4:
                out.append(error("STAIR_OVERLAP", [sa.id, sb.id], f"Stairs '{sa.id}' and '{sb.id}' overlap on {fl.name}."))
    return out
