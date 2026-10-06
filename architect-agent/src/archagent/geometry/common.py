"""Shared geometric helpers (plan view, metres, x = east, y = north)."""
from __future__ import annotations

import math
from typing import Tuple

from shapely.geometry import box

EPS = 1e-6
PROBE = 1e-3

# unit vector pointing from a room edge INTO the room
NORMAL_IN = {"south": (0.0, 1.0), "north": (0.0, -1.0), "west": (1.0, 0.0), "east": (-1.0, 0.0)}
RUN_VECTOR = {"north": (0.0, 1.0), "south": (0.0, -1.0), "east": (1.0, 0.0), "west": (-1.0, 0.0)}


def finite(*values) -> bool:
    return all(isinstance(v, (int, float)) and math.isfinite(v) for v in values)


def room_has_geometry(room) -> bool:
    return finite(room.x, room.y, room.width, room.depth) and room.width > EPS and room.depth > EPS


def room_box(room):
    return box(room.x, room.y, room.x + room.width, room.y + room.depth)


def edge_axis(side: str) -> str:
    """Axis the wall runs along: south/north walls run along x, east/west along y."""
    return "x" if side in ("south", "north") else "y"


def edge_start(room, side: str) -> float:
    return room.x if side in ("south", "north") else room.y


def edge_length(room, side: str) -> float:
    return room.width if side in ("south", "north") else room.depth


def edge_fixed(room, side: str) -> float:
    """Coordinate of the edge on the perpendicular axis."""
    return {"south": room.y, "north": room.y + room.depth, "west": room.x, "east": room.x + room.width}[side]


def point_on_edge(room, side: str, along: float, inward: float = 0.0) -> Tuple[float, float]:
    """Point at absolute coordinate ``along`` on the edge, shifted ``inward`` metres into the room."""
    nx, ny = NORMAL_IN[side]
    fixed = edge_fixed(room, side)
    if edge_axis(side) == "x":
        return (along + nx * inward, fixed + ny * inward)
    return (fixed + nx * inward, along + ny * inward)


def rect_contains(rect, p, tol=1e-9) -> bool:
    x0, y0, x1, y1 = rect
    return x0 - tol <= p[0] <= x1 + tol and y0 - tol <= p[1] <= y1 + tol


def r6(v: float) -> float:
    return round(v, 6)
