"""Floor slabs (union of room footprints minus stair openings)."""
from __future__ import annotations

from typing import List, Tuple

from shapely.geometry import box
from shapely.ops import unary_union

from .common import room_box, room_has_geometry


def slab_polygon(rooms, holes: List[tuple] = ()):
    polys = [room_box(r) for r in rooms if room_has_geometry(r)]
    if not polys:
        return None
    slab = unary_union(polys)
    for h in holes:
        slab = slab.difference(box(*h))
    return slab


def slab_cells(slab) -> List[Tuple[float, float, float, float]]:
    """Exact axis-aligned rectangle decomposition of a rectilinear polygon (with holes)."""
    if slab is None or slab.is_empty:
        return []
    xs, ys = set(), set()
    geoms = slab.geoms if slab.geom_type == "MultiPolygon" else [slab]
    for g in geoms:
        for ring in [g.exterior, *g.interiors]:
            for x, y in ring.coords:
                xs.add(round(x, 6))
                ys.add(round(y, 6))
    xs, ys = sorted(xs), sorted(ys)
    cells = []
    for y0, y1 in zip(ys, ys[1:]):
        run = None
        for x0, x1 in zip(xs, xs[1:]):
            inside = slab.covers(box(x0, y0, x1, y1).representative_point())
            if inside and run is not None:
                run = (run[0], y0, x1, y1)
            elif inside:
                run = (x0, y0, x1, y1)
            else:
                if run is not None:
                    cells.append(run)
                    run = None
        if run is not None:
            cells.append(run)
    return cells
