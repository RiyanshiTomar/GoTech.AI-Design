"""Stair geometry: step counts, boxes, headroom hole and arrival clearances."""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Optional, Tuple

from .common import finite

MAX_RISER = 0.19      # PoC practical limits (not a code citation)
MIN_TREAD = 0.25
MAX_TREAD = 0.30
MIN_LANE = 0.9
LANDING_CLEARANCE = 1.0

Box3 = Tuple[float, float, float, float, float, float]   # x0,y0,z0,x1,y1,z1 (z relative to floor level)


@dataclass
class StairGeo:
    id: str
    ok: bool
    problems: List[str]
    risers: int = 0
    riser: float = 0.0
    tread: float = 0.0
    required_length: float = 0.0
    required_width: float = 0.0
    footprint: Optional[tuple] = None
    boxes: Optional[List[Box3]] = None
    exit_rect: Optional[tuple] = None     # clearance needed on the floor above (x0,y0,x1,y1)
    entry_rect: Optional[tuple] = None    # clearance wanted on this floor


def _local_to_world(st, s0, s1, l0, l1):
    x, y, w, d = st.x, st.y, st.width, st.depth
    if st.direction == "north":
        return (x + l0, y + s0, x + l1, y + s1)
    if st.direction == "south":
        return (x + w - l1, y + d - s1, x + w - l0, y + d - s0)
    if st.direction == "east":
        return (x + s0, y + l0, x + s1, y + l1)
    return (x + w - s1, y + l0, x + w - s0, y + l1)   # west


def stair_geometry(st, floor_height: float) -> StairGeo:
    problems: List[str] = []
    if not finite(st.x, st.y, st.width, st.depth, floor_height) or st.width <= 0 or st.depth <= 0 or floor_height <= 0:
        return StairGeo(st.id, False, ["stair has non-numeric or non-positive dimensions"])
    if st.direction not in ("north", "south", "east", "west"):
        return StairGeo(st.id, False, [f"direction '{st.direction}' must be north, south, east or west"])
    if st.shape not in ("straight", "u"):
        return StairGeo(st.id, False, [f"shape '{st.shape}' must be 'straight' or 'u'"])

    along_x = st.direction in ("east", "west")
    run_len = st.width if along_x else st.depth       # available length along the run
    lat_w = st.depth if along_x else st.width         # available lateral width
    n = max(2, math.ceil(floor_height / MAX_RISER - 1e-9))
    riser = floor_height / n
    boxes: List[Box3] = []

    if st.shape == "straight":
        req_len = (n - 1) * MIN_TREAD
        req_wid = MIN_LANE
        if run_len + 1e-9 < req_len:
            problems.append(f"needs a run of at least {req_len:.2f} m for {n} risers but is only {run_len:.2f} m long")
        if lat_w + 1e-9 < req_wid:
            problems.append(f"needs a clear width of at least {req_wid:.2f} m but is only {lat_w:.2f} m wide")
        tread = min(MAX_TREAD, run_len / (n - 1)) if run_len > 0 else MIN_TREAD
        for k in range(1, n):
            boxes.append(_box(st, (k - 1) * tread, k * tread, 0, lat_w, k * riser))
        run_used = (n - 1) * tread
        exit_rect = _local_to_world(st, run_len, run_len + LANDING_CLEARANCE, 0, lat_w)
        entry_rect = _local_to_world(st, -MIN_LANE, 0, 0, lat_w)
        _ = run_used
    else:  # "u": two flights joined by a landing, arrival back on the start side
        n1 = math.ceil(n / 2)
        a, b = n1 - 1, n - n1 - 1
        gap = 0.1
        lane = (lat_w - gap) / 2
        landing = max(lane, MIN_LANE)
        req_len = a * MIN_TREAD + landing
        req_wid = 2 * MIN_LANE + gap
        if run_len + 1e-9 < req_len:
            problems.append(f"needs a run of at least {req_len:.2f} m (two flights + landing) but is only {run_len:.2f} m long")
        if lat_w + 1e-9 < req_wid:
            problems.append(f"needs a width of at least {req_wid:.2f} m (two lanes) but is only {lat_w:.2f} m wide")
        tread = min(MAX_TREAD, (run_len - landing) / max(a, 1)) if run_len > landing else MIN_TREAD
        for k in range(1, a + 1):
            boxes.append(_box(st, (k - 1) * tread, k * tread, 0, lane, k * riser))
        s_land = a * tread
        boxes.append(_box(st, s_land, s_land + landing, 0, lat_w, n1 * riser))
        for m in range(1, b + 1):
            boxes.append(_box(st, s_land - m * tread, s_land - (m - 1) * tread, lane + gap, lat_w, (n1 + m) * riser))
        exit_rect = _local_to_world(st, -LANDING_CLEARANCE, 0, lane + gap, lat_w)
        entry_rect = _local_to_world(st, -MIN_LANE, 0, 0, lane)

    footprint = (st.x, st.y, st.x + st.width, st.y + st.depth)
    return StairGeo(st.id, not problems, problems, n, riser, tread, req_len, req_wid, footprint, boxes, exit_rect, entry_rect)


def _box(st, s0, s1, l0, l1, z1) -> Box3:
    x0, y0, x1, y1 = _local_to_world(st, s0, s1, l0, l1)
    return (x0, y0, 0.0, x1, y1, z1)
