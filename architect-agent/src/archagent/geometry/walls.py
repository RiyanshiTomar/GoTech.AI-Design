"""Deterministic wall derivation.

Walls are never authored by the agent; they follow from the room rectangles:
  * every room edge becomes a wall segment (shared edges are merged),
  * a segment with enclosed rooms on both sides is INTERIOR (centred on the edge),
  * a segment with enclosed space on one side only is EXTERIOR (thickness is
    laid inward, so the outer face sits exactly on the room boundary and a
    building that is inside the plot has walls inside the plot),
  * wall pieces never overlap (corners are owned by the first piece).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple

from shapely.geometry import Point, box
from shapely.ops import unary_union

from .common import EPS, PROBE, r6, room_box, room_has_geometry


@dataclass
class WallPiece:
    id: str
    kind: str                       # "exterior" | "interior"
    x0: float
    y0: float
    x1: float
    y1: float
    axis: str                       # axis the wall runs along: "x" | "y"
    thickness: float
    seg: Tuple[Tuple[float, float], Tuple[float, float]]   # original centre-line segment
    rooms: List[str] = field(default_factory=list)
    regular: bool = True            # False when the piece could not be made a clean rectangle

    @property
    def rect(self):
        return (self.x0, self.y0, self.x1, self.y1)

    @property
    def length(self) -> float:
        return max(self.x1 - self.x0, self.y1 - self.y0)

    def seg_range(self) -> Tuple[float, float]:
        (ax, ay), (bx, by) = self.seg
        return (min(ax, bx), max(ax, bx)) if self.axis == "x" else (min(ay, by), max(ay, by))


def _edges(room):
    x0, y0, x1, y1 = room.bounds()
    return [((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)), ((x0, y1), (x1, y1)), ((x0, y0), (x0, y1))]


def _norm(seg):
    a, b = seg
    a, b = (r6(a[0]), r6(a[1])), (r6(b[0]), r6(b[1]))
    return (a, b) if a <= b else (b, a)


def _split_edges(rooms) -> Dict[tuple, set]:
    """Node every room edge at other rooms' corners and dedupe shared sub-segments."""
    verts = {(r6(v[0]), r6(v[1])) for r in rooms for e in _edges(r) for v in e}
    segs: Dict[tuple, set] = {}
    for room in rooms:
        for (a, b) in _edges(room):
            a, b = (r6(a[0]), r6(a[1])), (r6(b[0]), r6(b[1]))
            horizontal = a[1] == b[1]
            lo, hi = (min(a[0], b[0]), max(a[0], b[0])) if horizontal else (min(a[1], b[1]), max(a[1], b[1]))
            cuts = {lo, hi}
            for v in verts:
                c, along = (v[1], v[0]) if horizontal else (v[0], v[1])
                fixed = a[1] if horizontal else a[0]
                if abs(c - fixed) < EPS and lo + EPS < along < hi - EPS:
                    cuts.add(along)
            pts = sorted(cuts)
            for p, q in zip(pts, pts[1:]):
                s = ((p, a[1]), (q, a[1])) if horizontal else ((a[0], p), (a[0], q))
                segs.setdefault(_norm(s), set()).add(room.id)
    return segs


def _merge_collinear(items: List[dict]) -> List[dict]:
    """Merge touching collinear segments with identical attributes at degree-2 nodes."""
    degree: Dict[tuple, int] = {}
    for it in items:
        for p in it["seg"]:
            degree[p] = degree.get(p, 0) + 1
    changed = True
    while changed:
        changed = False
        items.sort(key=lambda i: (i["axis"], i["fixed"], i["lo"]))
        for i, a in enumerate(items):
            for j in range(i + 1, len(items)):
                b = items[j]
                if (a["axis"], a["fixed"]) != (b["axis"], b["fixed"]):
                    break
                if abs(a["hi"] - b["lo"]) < EPS and a["key"] == b["key"]:
                    node = a["seg"][1]
                    if degree.get(node, 0) == 2:
                        merged = dict(a)
                        merged["hi"] = b["hi"]
                        merged["seg"] = _norm((a["seg"][0], b["seg"][1]))
                        items[i] = merged
                        del items[j]
                        degree[node] = 0
                        changed = True
                        break
            if changed:
                break
    return items


def _rect_of(poly):
    """Return (rect, regular) for a shapely geometry that should be an axis-aligned rectangle."""
    if poly.is_empty:
        return None, True
    if poly.geom_type == "MultiPolygon":
        poly = max(poly.geoms, key=lambda g: g.area)
    if poly.geom_type != "Polygon":
        return None, False
    minx, miny, maxx, maxy = poly.bounds
    regular = abs(poly.area - (maxx - minx) * (maxy - miny)) < 1e-6
    return (minx, miny, maxx, maxy), regular


def _wall_id(floor_id, it) -> str:
    """Stable id from the wall's own centre line (cm), e.g. 'ground-wall-x100-500-900'.
    Unlike an index, it does not change when an unrelated room is edited."""
    c = lambda v: int(round(v * 100))
    return f"{floor_id}-wall-{it['axis']}{c(it['fixed'])}-{c(it['lo'])}-{c(it['hi'])}"


def derive_walls(floor_id: str, rooms, t_ext: float, t_int: float) -> List[WallPiece]:
    enclosed = [r for r in rooms if not r.is_open and room_has_geometry(r)]
    if not enclosed or not (t_ext > 0 and t_int > 0):
        return []
    boxes = {r.id: room_box(r) for r in enclosed}
    footprint = unary_union(list(boxes.values()))
    segs = _split_edges(enclosed)

    items = []
    for seg, owners in segs.items():
        (ax, ay), (bx, by) = seg
        horizontal = ay == by
        axis = "x" if horizontal else "y"
        fixed = ay if horizontal else ax
        lo, hi = (ax, bx) if horizontal else (ay, by)
        mx, my = (ax + bx) / 2, (ay + by) / 2
        n = (0.0, 1.0) if horizontal else (1.0, 0.0)
        p_pos = Point(mx + n[0] * PROBE, my + n[1] * PROBE)
        p_neg = Point(mx - n[0] * PROBE, my - n[1] * PROBE)
        in_pos, in_neg = footprint.covers(p_pos), footprint.covers(p_neg)
        if in_pos and in_neg:
            kind, inward = "interior", 0.0
        elif in_pos or in_neg:
            kind, inward = "exterior", (1.0 if in_pos else -1.0)
        else:
            continue
        rooms_here = set(owners)
        for rid, b in boxes.items():
            if b.covers(p_pos) or b.covers(p_neg):
                rooms_here.add(rid)
        items.append({"seg": seg, "axis": axis, "fixed": fixed, "lo": lo, "hi": hi, "kind": kind,
                      "inward": inward, "rooms": rooms_here,
                      "key": (kind, inward, frozenset(rooms_here))})
    items = _merge_collinear(items)
    items.sort(key=lambda i: (0 if i["kind"] == "exterior" else 1, i["axis"], i["fixed"], i["lo"]))

    ring = footprint.difference(footprint.buffer(-t_ext, join_style=2))
    pieces: List[WallPiece] = []
    taken = None
    for idx, it in enumerate(items):
        lo, hi, fixed = it["lo"], it["hi"], it["fixed"]
        if it["kind"] == "exterior":
            ext = t_ext
            a0, a1 = lo - ext, hi + ext
            f0, f1 = (fixed, fixed + ext) if it["inward"] > 0 else (fixed - ext, fixed)
            raw = box(a0, f0, a1, f1) if it["axis"] == "x" else box(f0, a0, f1, a1)
            geom = raw.intersection(ring)
        else:
            h = t_int / 2
            a0, a1 = lo - h, hi + h
            raw = box(a0, fixed - h, a1, fixed + h) if it["axis"] == "x" else box(fixed - h, a0, fixed + h, a1)
            geom = raw.intersection(footprint)
        if taken is not None:
            geom = geom.difference(taken)
        rect, regular = _rect_of(geom)
        if rect is None or (rect[2] - rect[0]) < EPS or (rect[3] - rect[1]) < EPS:
            continue
        piece_poly = box(*rect)
        taken = piece_poly if taken is None else unary_union([taken, piece_poly])
        thickness = min(rect[2] - rect[0], rect[3] - rect[1])
        pieces.append(WallPiece(
            id=_wall_id(floor_id, it), kind=it["kind"],
            x0=rect[0], y0=rect[1], x1=rect[2], y1=rect[3], axis=it["axis"], thickness=thickness,
            seg=it["seg"], rooms=sorted(it["rooms"]), regular=regular))
    return pieces
