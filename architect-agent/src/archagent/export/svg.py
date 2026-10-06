"""Deterministic SVG floor plans. The LLM never writes SVG; this converts the model into it."""
from __future__ import annotations

import math
from typing import List
from xml.sax.saxutils import escape

from ..geometry import analyze
from ..geometry.common import NORMAL_IN, finite

SCALE = 50.0      # px per metre
MARGIN = 70.0

STYLE = """
.site{fill:#fafaf7;stroke:#9a9a92;stroke-width:1.5;stroke-dasharray:8 5}
.footprint{fill:none;stroke:#222;stroke-width:1}
.room{fill:#f3efe6;stroke:none}
.room.open{fill:#e4ecdc}
.room-name{font:600 12px sans-serif;fill:#222;text-anchor:middle}
.room-dim{font:11px sans-serif;fill:#666;text-anchor:middle}
.wall{fill:#1d1d1b;stroke:none}
.opening-gap{fill:#fff;stroke:none}
.door-leaf{stroke:#1d1d1b;stroke-width:2;fill:none}
.door-swing{stroke:#777;stroke-width:1;fill:none}
.window{stroke:#3b7ea1;stroke-width:3;fill:none}
.stair-box{fill:#fff;stroke:#444;stroke-width:1}
.stair-step{stroke:#777;stroke-width:1}
.stair-arrow{stroke:#444;stroke-width:1.5;fill:none}
.dim{stroke:#555;stroke-width:1;fill:none}
.dim-text{font:11px sans-serif;fill:#333;text-anchor:middle}
.title{font:700 15px sans-serif;fill:#111}
"""


class _T:
    def __init__(self, depth: float):
        self.h = depth

    def x(self, v): return MARGIN + v * SCALE
    def y(self, v): return MARGIN + (self.h - v) * SCALE
    def p(self, x, y): return (self.x(x), self.y(y))


def _rect(t, r, cls, extra=""):
    x0, y0, x1, y1 = r
    return (f'<rect class="{cls}" {extra} x="{t.x(x0):.1f}" y="{t.y(y1):.1f}" '
            f'width="{(x1 - x0) * SCALE:.1f}" height="{(y1 - y0) * SCALE:.1f}"/>')


def _dim_line(t, p0, p1, offset_px, label, horizontal):
    (x0, y0), (x1, y1) = t.p(*p0), t.p(*p1)
    if horizontal:
        y0 += offset_px; y1 += offset_px
        tx, ty = (x0 + x1) / 2, y0 - 4
        ticks = f'M{x0:.1f},{y0 - 5:.1f}V{y0 + 5:.1f}M{x1:.1f},{y1 - 5:.1f}V{y1 + 5:.1f}'
    else:
        x0 += offset_px; x1 += offset_px
        tx, ty = x0 - 6, (y0 + y1) / 2
        ticks = f'M{x0 - 5:.1f},{y0:.1f}H{x0 + 5:.1f}M{x1 - 5:.1f},{y1:.1f}H{x1 + 5:.1f}'
    rot = "" if horizontal else f' transform="rotate(-90 {tx:.1f} {ty:.1f})"'
    return (f'<path class="dim" d="M{x0:.1f},{y0:.1f}L{x1:.1f},{y1:.1f}{ticks}"/>'
            f'<text class="dim-text" x="{tx:.1f}" y="{ty:.1f}"{rot}>{label}</text>')


def _door(t, op, wall):
    """Gap in the wall + leaf + swing arc."""
    out = [_rect(t, op.rect, "opening-gap", f'id="gap-{op.id}"')]
    if op.leafless or op.kind != "door" or wall is None:
        return out
    nx, ny = NORMAL_IN[op.side]
    if op.swing == "out":
        nx, ny = -nx, -ny
    w = op.width
    if op.axis == "x":
        cy = (wall.y0 + wall.y1) / 2
        ends = {"left": op.a0, "right": op.a1}
        hx = ends[op.hinge]; hy = cy
        cx = op.a1 if op.hinge == "left" else op.a0; cy2 = cy
    else:
        cx_ = (wall.x0 + wall.x1) / 2
        ends = {"left": op.a0, "right": op.a1}
        hx = cx_; hy = ends[op.hinge]
        cx = cx_; cy2 = op.a1 if op.hinge == "left" else op.a0
    tipx, tipy = hx + nx * w, hy + ny * w
    H, C, T = t.p(hx, hy), t.p(cx, cy2), t.p(tipx, tipy)
    cross = (C[0] - H[0]) * (T[1] - H[1]) - (C[1] - H[1]) * (T[0] - H[0])
    sweep = 1 if cross > 0 else 0
    r = w * SCALE
    out.append(f'<line class="door-leaf" x1="{H[0]:.1f}" y1="{H[1]:.1f}" x2="{T[0]:.1f}" y2="{T[1]:.1f}"/>')
    out.append(f'<path class="door-swing" d="M{C[0]:.1f},{C[1]:.1f}A{r:.1f},{r:.1f} 0 0 {sweep} {T[0]:.1f},{T[1]:.1f}"/>')
    return out


def _window(t, op, wall):
    out = [_rect(t, op.rect, "opening-gap", f'id="gap-{op.id}"')]
    if wall is None:
        return out
    if op.axis == "x":
        cy = (wall.y0 + wall.y1) / 2
        (x0, y0), (x1, y1) = t.p(op.a0, cy), t.p(op.a1, cy)
    else:
        cx = (wall.x0 + wall.x1) / 2
        (x0, y0), (x1, y1) = t.p(cx, op.a0), t.p(cx, op.a1)
    out.append(f'<line class="window" x1="{x0:.1f}" y1="{y0:.1f}" x2="{x1:.1f}" y2="{y1:.1f}"/>')
    return out


def _stair(t, st, geo, label):
    if geo.footprint is None:
        return []
    out = [_rect(t, geo.footprint, "stair-box")]
    for b in geo.boxes or []:
        x0, y0, _, x1, y1, _ = b
        out.append(_rect(t, (x0, y0, x1, y1), "stair-step", 'style="fill:none"'))
    fx0, fy0, fx1, fy1 = geo.footprint
    cx, cy = (fx0 + fx1) / 2, (fy0 + fy1) / 2
    dx, dy = {"north": (0, 1), "south": (0, -1), "east": (1, 0), "west": (-1, 0)}[st.direction]
    ln = (max(fx1 - fx0, fy1 - fy0)) * 0.35
    a, b = t.p(cx - dx * ln, cy - dy * ln), t.p(cx + dx * ln, cy + dy * ln)
    out.append(f'<path class="stair-arrow" d="M{a[0]:.1f},{a[1]:.1f}L{b[0]:.1f},{b[1]:.1f}"/>')
    out.append(f'<text class="room-dim" x="{t.x(cx):.1f}" y="{t.y(fy0) - 6:.1f}">{label}</text>')
    return out


def render_floor_svg(model, floor_id: str) -> str:
    an = analyze(model)
    fg = an.floor_geo(floor_id)
    if fg is None:
        raise ValueError(f"unknown floor '{floor_id}'")
    b = an.building
    if not (finite(b.width, b.depth) and b.width > 0 and b.depth > 0):
        raise ValueError("site has no valid dimensions; cannot render")
    t = _T(b.depth)
    W, H = b.width * SCALE + 2 * MARGIN, b.depth * SCALE + 2 * MARGIN + 30
    wall_by_id = {w.id: w for w in fg.walls}
    body: List[str] = []
    body.append(f'<text class="title" x="{MARGIN}" y="26">{escape(b.name or "Building")} - {escape(fg.floor.name)}</text>')
    body.append(_rect(t, (0, 0, b.width, b.depth), "site", 'id="site-boundary"'))
    if an.site is not None and b.setback:
        body.append(_rect(t, (b.setback, b.setback, b.width - b.setback, b.depth - b.setback), "dim", 'id="setback-line" style="fill:none"'))

    body.append('<g id="rooms">')
    for r in fg.rooms.values():
        if r.id not in fg.boxes:
            continue
        cls = "room open" if r.is_open else "room"
        body.append(f'<g id="room-{r.id}" data-kind="{r.kind}">' + _rect(t, r.bounds(), cls) +
                    f'<text class="room-name" x="{t.x(r.x + r.width / 2):.1f}" y="{t.y(r.y + r.depth / 2) - 2:.1f}">{escape(r.name)}</text>'
                    f'<text class="room-dim" x="{t.x(r.x + r.width / 2):.1f}" y="{t.y(r.y + r.depth / 2) + 12:.1f}">'
                    f'{r.width:.2f} x {r.depth:.2f} m</text></g>')
    body.append('</g>')

    body.append('<g id="walls">')
    for w in fg.walls:
        body.append(_rect(t, w.rect, "wall", f'id="wall-{w.id}" data-kind="{w.kind}"'))
    body.append('</g>')

    body.append('<g id="openings">')
    for op in fg.openings:
        if op.rect is None or op.problems and op.wall_id is None:
            continue
        wall = wall_by_id.get(op.wall_id)
        parts = _door(t, op, wall) if op.kind == "door" else _window(t, op, wall)
        body.append(f'<g id="{op.kind}-{op.id}">' + "".join(parts) + '</g>')
    body.append('</g>')

    body.append('<g id="stairs">')
    for st in fg.floor.stairs:
        geo = fg.stairs.get(st.id)
        if geo:
            body.append(f'<g id="stair-{st.id}">' + "".join(_stair(t, st, geo, "UP")) + '</g>')
    # arrival of stairs from the floor below
    idx = an.floors.index(fg)
    if idx > 0:
        for st in an.floors[idx - 1].floor.stairs:
            geo = an.floors[idx - 1].stairs.get(st.id)
            if geo and geo.footprint:
                body.append(f'<g id="stair-{st.id}-arrival">' + _rect(t, geo.footprint, "stair-box", 'style="fill:none;stroke-dasharray:4 3"') +
                            f'<text class="room-dim" x="{t.x((geo.footprint[0] + geo.footprint[2]) / 2):.1f}" '
                            f'y="{t.y((geo.footprint[1] + geo.footprint[3]) / 2):.1f}">DN</text></g>')
    body.append('</g>')

    # overall dimensions
    body.append('<g id="dimensions">')
    if fg.boxes:
        from shapely.ops import unary_union
        minx, miny, maxx, maxy = unary_union(list(fg.boxes.values())).bounds
        body.append(_dim_line(t, (minx, miny), (maxx, miny), 24, f"{maxx - minx:.2f} m", True))
        body.append(_dim_line(t, (minx, miny), (minx, maxy), -24, f"{maxy - miny:.2f} m", False))
    body.append(_dim_line(t, (0, 0), (b.width, 0), 48, f"site {b.width:.2f} m", True))
    body.append(_dim_line(t, (0, 0), (0, b.depth), -48, f"site {b.depth:.2f} m", False))
    body.append('</g>')

    return (f'<svg xmlns="http://www.w3.org/2000/svg" id="floorplan-{fg.floor.id}" viewBox="0 0 {W:.0f} {H:.0f}" '
            f'width="{W:.0f}" height="{H:.0f}"><style>{STYLE}</style>'
            f'<rect width="100%" height="100%" fill="#fff"/>' + "".join(body) + '</svg>')


def render_all_svgs(model, out_dir) -> List[str]:
    import os
    os.makedirs(out_dir, exist_ok=True)
    an = analyze(model)
    paths = []
    for fg in an.floors:
        p = os.path.join(out_dir, f"floorplan-{fg.floor.id}.svg")
        with open(p, "w", encoding="utf-8") as f:
            f.write(render_floor_svg(model, fg.floor.id))
        paths.append(p)
    return paths
