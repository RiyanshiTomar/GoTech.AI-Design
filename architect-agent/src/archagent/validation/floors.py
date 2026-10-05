"""Relationships between floors."""
from __future__ import annotations

from shapely.ops import unary_union

from ..geometry.common import room_box, room_has_geometry
from .issues import error


def validate_floor_support(an):
    out = []
    for i in range(1, len(an.floors)):
        below, fg = an.floors[i - 1], an.floors[i]
        under = [room_box(r) for r in below.rooms.values() if room_has_geometry(r)]
        if not under:
            continue
        support = unary_union(under).buffer(1e-6)
        for r in fg.rooms.values():
            if r.is_open or not room_has_geometry(r):
                continue
            hang = room_box(r).difference(support).area
            if hang > 1e-3:
                out.append(error("UPPER_ROOM_UNSUPPORTED", [f"{r.name} ({fg.floor.name})"],
                                 f"{r.name} on {fg.floor.name} overhangs the floor below by {hang:.2f} square metres. Upper footprints must sit on the floor below (use a balcony/terrace for overhangs).",
                                 hint=f"Keep upper rooms within the footprint of {below.floor.name}.", data={"overhang_area": round(hang, 3)}))
    return out
