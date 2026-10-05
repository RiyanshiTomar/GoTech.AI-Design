"""Structure, units, ids and dimension sanity."""
from __future__ import annotations

from collections import Counter

from ..geometry.common import finite
from . import rules
from .issues import error, warning


def validate_units(an):
    """Problems recorded by the SDK while parsing lengths/units/programme."""
    return [error(i["code"], i.get("objects", []), i["details"]) for i in an.building.issues]


def validate_duplicate_ids(an):
    out = []
    ids = Counter(f.id for f in an.building.floors)
    for fid, n in ids.items():
        if n > 1:
            out.append(error("DUPLICATE_ID", [fid], f"Floor id '{fid}' is used {n} times."))
    for fl in an.building.floors:
        for label, recs in (("room", fl.rooms), ("door", fl.doors), ("window", fl.windows), ("stair", fl.stairs)):
            for rid, n in Counter(r.id for r in recs).items():
                if n > 1:
                    out.append(error("DUPLICATE_ID", [rid], f"{label.capitalize()} id '{rid}' is used {n} times on {fl.name}.",
                                     hint="Give every element a unique id."))
        for name, n in Counter(r.name.lower() for r in fl.rooms).items():
            if n > 1:
                out.append(warning("DUPLICATE_NAME", [name], f"{n} rooms on {fl.name} are called '{name}'. Use distinct names so follow-up edits are unambiguous."))
    return out


def validate_site(an):
    b = an.building
    out = []
    for label, v in (("width", b.width), ("depth", b.depth)):
        if not finite(v):
            out.append(error("INVALID_DIMENSION", ["site"], f"Plot {label} is not a valid number."))
        elif v <= 0:
            out.append(error("NONPOSITIVE_DIMENSION", ["site"], f"Plot {label} is {v:g} m; it must be greater than zero."))
        elif v < rules.MIN_SITE_M:
            out.append(error("EXTREME_DIMENSION", ["site"], f"Plot {label} {v:g} m is too small to build on (minimum {rules.MIN_SITE_M:g} m)."))
        elif v > rules.MAX_SITE_M:
            out.append(error("EXTREME_DIMENSION", ["site"], f"Plot {label} {v:g} m is unrealistically large (maximum {rules.MAX_SITE_M:g} m for this tool). Check the units."))
    if not finite(b.setback) or b.setback < 0:
        out.append(error("INVALID_DIMENSION", ["site"], f"Setback {b.setback!r} must be zero or positive."))
    elif finite(b.width, b.depth) and (b.width - 2 * b.setback <= 0 or b.depth - 2 * b.setback <= 0):
        out.append(error("SETBACK_TOO_LARGE", ["site"], f"Setback {b.setback:g} m leaves no buildable area on a {b.width:g} x {b.depth:g} m plot."))
    lo, hi = rules.WALL_THICKNESS_EXT
    if not finite(b.wall_exterior) or not lo <= b.wall_exterior <= hi:
        out.append(error("WALL_THICKNESS_INVALID", ["wall_exterior"], f"Exterior wall thickness {b.wall_exterior!r} m must be between {lo} and {hi} m."))
    lo, hi = rules.WALL_THICKNESS_INT
    if not finite(b.wall_interior) or not lo <= b.wall_interior <= hi:
        out.append(error("WALL_THICKNESS_INVALID", ["wall_interior"], f"Interior wall thickness {b.wall_interior!r} m must be between {lo} and {hi} m."))
    return out


def validate_floors(an):
    b = an.building
    out = []
    if not b.floors:
        return [error("NO_FLOORS", ["building"], "The building has no floors. Call building.add_floor(...).")]
    if len(b.floors) > rules.MAX_FLOORS_HARD:
        out.append(error("TOO_MANY_FLOORS", ["building"], f"{len(b.floors)} floors exceeds the tool limit of {rules.MAX_FLOORS_HARD}."))
    elif len(b.floors) > b.max_floors:
        out.append(error("TOO_MANY_FLOORS", ["building"], f"{len(b.floors)} floors but max_floors={b.max_floors}.",
                         hint="Only raise max_floors if the user explicitly allows more storeys."))
    prev = None
    lo, hi = rules.FLOOR_HEIGHT
    for fg in an.floors:
        fl = fg.floor
        if not finite(fl.height) or not lo <= fl.height <= hi:
            out.append(error("FLOOR_HEIGHT_INVALID", [fl.name], f"Floor-to-floor height {fl.height!r} m must be between {lo} and {hi} m."))
        if not finite(fl.elevation):
            out.append(error("INVALID_VALUE", [fl.name], "Floor elevation is not a number."))
        elif prev is not None and finite(prev.elevation, prev.height) and abs(fl.elevation - (prev.elevation + prev.height)) > 1e-6:
            out.append(error("ELEVATION_MISMATCH", [prev.name, fl.name],
                             f"{fl.name} starts at {fl.elevation:g} m but {prev.name} ends at {prev.elevation + prev.height:g} m.",
                             hint="Omit elevation in add_floor() to stack floors automatically."))
        if not fl.rooms:
            out.append(error("EMPTY_FLOOR", [fl.name], f"{fl.name} has no rooms."))
        prev = fl
    return out
