"""Room geometry: dimensions, polygon validity, site/floor bounds, overlaps."""
from __future__ import annotations

from itertools import combinations

from shapely.geometry import box

from ..geometry.common import EPS, finite, room_box, room_has_geometry
from . import rules
from .issues import error


def _label(an, fl, room):
    return f"{room.name} ({fl.name})" if len(an.building.floors) > 1 else room.name


def allowed_region(an):
    """Buildable area = plot minus setbacks (hard boundary for every element)."""
    b = an.building
    if not finite(b.width, b.depth, b.setback):
        return None
    x0, y0, x1, y1 = b.setback, b.setback, b.width - b.setback, b.depth - b.setback
    return box(x0, y0, x1, y1) if x1 > x0 and y1 > y0 else None


def validate_room_dimensions(an):
    out = []
    for fg in an.floors:
        fl = fg.floor
        for r in fl.rooms:
            lab = _label(an, fl, r)
            if not finite(r.x, r.y, r.width, r.depth):
                out.append(error("INVALID_VALUE", [lab], f"{lab} has a non-numeric position or size."))
                continue
            if r.width <= 0 or r.depth <= 0:
                code = "ZERO_DIMENSION" if (r.width == 0 or r.depth == 0) else "NEGATIVE_DIMENSION"
                out.append(error(code, [lab], f"{lab} has width {r.width:g} m and depth {r.depth:g} m; both must be greater than zero."))
                continue
            if r.width > rules.MAX_SITE_M or r.depth > rules.MAX_SITE_M:
                out.append(error("EXTREME_DIMENSION", [lab], f"{lab} is {r.width:g} x {r.depth:g} m, which is unrealistically large. Check the units."))
                continue
            minimum = an.building.min_dims.get(r.kind, rules.MIN_SIDE.get(r.kind, rules.MIN_SIDE["default"]))
            if min(r.width, r.depth) + EPS < minimum:
                code = "CORRIDOR_TOO_NARROW" if r.kind == "corridor" else "MIN_DIMENSION"
                out.append(error(code, [lab], f"{lab} is {r.width:g} x {r.depth:g} m; its narrow side must be at least {minimum:g} m for a {r.kind}.",
                                 data={"kind": r.kind, "min_side": minimum}))
            if not box(r.x, r.y, r.x + r.width, r.y + r.depth).is_valid:
                out.append(error("INVALID_POLYGON", [lab], f"{lab} does not form a valid polygon."))
    return out


def validate_bounds(an):
    """Site bounds + floor/building boundary (plot minus setback), with exact overshoot per side."""
    out = []
    b = an.building
    allowed = allowed_region(an)
    if allowed is None:
        return out
    ax0, ay0, ax1, ay1 = allowed.bounds
    for fg in an.floors:
        fl = fg.floor
        for r in fl.rooms:
            if not room_has_geometry(r):
                continue
            lab = _label(an, fl, r)
            over = {}
            if r.x < ax0 - EPS:
                over["west"] = ax0 - r.x
            if r.x + r.width > ax1 + EPS:
                over["east"] = r.x + r.width - ax1
            if r.y < ay0 - EPS:
                over["south"] = ay0 - r.y
            if r.y + r.depth > ay1 + EPS:
                over["north"] = r.y + r.depth - ay1
            if over:
                inside_site = (r.x >= -EPS and r.y >= -EPS and r.x + r.width <= b.width + EPS and r.y + r.depth <= b.depth + EPS)
                parts = ", ".join(f"{side} boundary by {v:.2f} m" for side, v in over.items())
                code = "OUT_OF_BOUNDS" if inside_site else "ROOM_OUTSIDE_SITE"
                where = "the setback line" if inside_site and b.setback > 0 else "the plot"
                out.append(error(code, [lab], f"{lab} exceeds {parts} (allowed area is x {ax0:g}-{ax1:g} m, y {ay0:g}-{ay1:g} m; {where}).",
                                 hint="Move or shrink the room so that x >= %g, y >= %g, x+width <= %g, y+depth <= %g." % (ax0, ay0, ax1, ay1),
                                 data={"overshoot": {k: round(v, 3) for k, v in over.items()}, "allowed": [ax0, ay0, ax1, ay1]}))
    return out


def validate_overlaps(an):
    out = []
    for fg in an.floors:
        fl = fg.floor
        items = [(r, room_box(r)) for r in fl.rooms if room_has_geometry(r)]
        for (ra, pa), (rb, pb) in combinations(items, 2):
            if ra.id == rb.id:
                continue
            area = pa.intersection(pb).area
            if area > 1e-4:
                la, lb = _label(an, fl, ra), _label(an, fl, rb)
                out.append(error("ROOM_OVERLAP", [la, lb], f"{la} and {lb} overlap by {area:.2f} square metres.",
                                 hint="Rooms may touch along an edge but must not share area.",
                                 data={"overlap_area": round(area, 3)}))
    return out
