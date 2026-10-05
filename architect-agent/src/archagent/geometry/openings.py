"""Resolve doors / windows to concrete wall pieces. Problems are recorded, not raised."""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .common import (NORMAL_IN, PROBE, edge_axis, edge_fixed, edge_length, edge_start, finite, point_on_edge,
                     rect_contains)
from .walls import WallPiece
from ..core.entities import SIDES


@dataclass
class Opening:
    id: str
    kind: str                     # "door" | "window"
    room: str
    side: str
    axis: str                     # axis the wall runs along
    a0: float                     # opening interval along the wall axis (absolute coords)
    a1: float
    z0: float                     # bottom / top relative to floor level
    z1: float
    wall_id: Optional[str] = None
    rect: Optional[tuple] = None  # plan rectangle cut through the wall
    connects: Optional[str] = None   # room on the other side (None = outside)
    swing: str = "in"
    hinge: str = "left"
    leafless: bool = False
    entrance: bool = False
    expect_connects: Optional[str] = None
    problems: List[Dict[str, str]] = field(default_factory=list)

    @property
    def width(self) -> float:
        return self.a1 - self.a0

    @property
    def center(self) -> float:
        return (self.a0 + self.a1) / 2


def _problem(op: Opening, code: str, details: str):
    op.problems.append({"code": code, "details": details})


def resolve_openings(floor, rooms_by_id: Dict[str, object], boxes: Dict[str, object],
                     walls: List[WallPiece], t_ext: float, t_int: float) -> List[Opening]:
    clear = max(t_ext, t_int / 2) + 0.05 if finite(t_ext, t_int) else 0.3
    out: List[Opening] = []
    records = [("door", d) for d in floor.doors] + [("window", w) for w in floor.windows]
    for kind, rec in records:
        z0, z1 = (0.0, rec.height) if kind == "door" else (rec.sill, rec.sill + rec.height)
        op = Opening(id=rec.id, kind=kind, room=rec.room, side=rec.side, axis=edge_axis(rec.side) if rec.side in SIDES else "x",
                     a0=math.nan, a1=math.nan, z0=z0, z1=z1)
        if kind == "door":
            op.swing, op.hinge, op.leafless = rec.swing, rec.hinge, rec.open
            op.entrance, op.expect_connects = rec.entrance, rec.expect_connects
        out.append(op)
        room = rooms_by_id.get(rec.room)
        if room is None:
            _problem(op, "UNKNOWN_ROOM", f"{kind} '{rec.id}' refers to room '{rec.room}', which does not exist on {floor.name}.")
            continue
        if rec.side not in SIDES:
            _problem(op, "INVALID_SIDE", f"{kind} '{rec.id}' has side '{rec.side}'. Use one of {', '.join(SIDES)}.")
            continue
        if room.is_open:
            _problem(op, f"{kind.upper()}_NOT_ON_WALL", f"{room.name} is an open space ({room.kind}) and has no walls to hold a {kind}.")
            continue
        if not finite(rec.offset, rec.width) or not finite(room.x, room.y, room.width, room.depth) or rec.width <= 0:
            _problem(op, "INVALID_VALUE", f"{kind} '{rec.id}' has a non-numeric or non-positive offset/width.")
            continue
        start, length = edge_start(room, rec.side), edge_length(room, rec.side)
        op.a0, op.a1 = start + rec.offset, start + rec.offset + rec.width
        if rec.offset < -1e-9 or rec.offset + rec.width > length + 1e-9:
            _problem(op, "OPENING_OUT_OF_EDGE",
                     f"{kind} '{rec.id}' spans {rec.offset:.2f}-{rec.offset + rec.width:.2f} m along the {rec.side} wall of "
                     f"{room.name}, but that wall is only {length:.2f} m long.")
            continue
        centre = (op.a0 + op.a1) / 2
        probe = point_on_edge(room, rec.side, centre, PROBE)
        wall = next((w for w in walls if rect_contains(w.rect, probe)), None)
        if wall is None:
            _problem(op, f"{kind.upper()}_NOT_ON_WALL",
                     f"No wall exists at the {rec.side} side of {room.name} at {rec.offset:.2f} m; the {kind} is not attached to a wall.")
            continue
        op.wall_id = wall.id
        lo, hi = wall.seg_range()
        if rec.width > (hi - lo) + 1e-9 or (hi - lo) < rec.width + 2 * clear - 1e-9:
            code = f"{kind.upper()}_TOO_WIDE" if rec.width > (hi - lo) - 2 * clear + 1e-9 else "OPENING_OUT_OF_WALL"
            _problem(op, code, f"{kind} '{rec.id}' ({rec.width:.2f} m) does not fit the wall segment it is on "
                               f"({hi - lo:.2f} m long, {2 * clear:.2f} m is needed for corners/junctions).")
        elif op.a0 < lo + clear - 1e-9 or op.a1 > hi - clear + 1e-9:
            _problem(op, "OPENING_OUT_OF_WALL",
                     f"{kind} '{rec.id}' is within {clear:.2f} m of a wall corner/junction; keep it at least that far from "
                     f"the ends of the wall segment ({lo:.2f}-{hi:.2f} m).")
        if rec.side in ("south", "north"):
            op.rect = (op.a0, wall.y0, op.a1, wall.y1)
        else:
            op.rect = (wall.x0, op.a0, wall.x1, op.a1)
        far = point_on_edge(room, rec.side, centre, -PROBE)
        op.connects = next((rid for rid, b in boxes.items() if rid != room.id and b.covers(_pt(far))), None)
    return out


def _pt(p):
    from shapely.geometry import Point
    return Point(p[0], p[1])
