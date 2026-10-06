"""Wall validity."""
from __future__ import annotations

from ..geometry.common import finite, room_has_geometry
from .issues import error


def validate_walls(an):
    out = []
    b = an.building
    for fg in an.floors:
        fl = fg.floor
        for w in fg.walls:
            if not w.regular:
                out.append(error("WALL_INVALID_POLYGON", [w.id], f"Wall {w.id} on {fl.name} does not form a clean rectangle (rooms: {', '.join(w.rooms)}).",
                                 hint="Avoid rooms that only touch at a corner or overlap partially."))
            if w.length < w.thickness - 1e-9:
                out.append(error("WALL_INVALID_POLYGON", [w.id], f"Wall {w.id} on {fl.name} is shorter than it is thick."))
        if finite(b.wall_exterior):
            for r in fl.rooms:
                if room_has_geometry(r) and not r.is_open and min(r.width, r.depth) - b.wall_exterior < 0.5:
                    out.append(error("WALL_THICKNESS_TOO_LARGE", [r.name],
                                     f"With {b.wall_exterior:g} m walls, {r.name} ({r.width:g} x {r.depth:g} m) has under 0.5 m clear space.",
                                     hint="Reduce wall thickness or enlarge the room."))
    return out
