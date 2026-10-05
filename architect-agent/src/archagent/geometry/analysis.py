"""One pass that turns the model dict into all derived geometry.

Validators and exporters both consume ``Analysis`` so they can never disagree
about where walls, openings, slabs or stairs are.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from shapely.geometry import box

from ..core import Building
from ..core.floor import Floor
from .common import finite, room_box, room_has_geometry
from .openings import Opening, resolve_openings
from .slabs import slab_polygon
from .stairs import StairGeo, stair_geometry
from .walls import WallPiece, derive_walls


@dataclass
class FloorGeo:
    floor: Floor
    rooms: Dict[str, object]
    boxes: Dict[str, object]            # shapely polygons of rooms with valid geometry
    walls: List[WallPiece]
    openings: List[Opening]
    stairs: Dict[str, StairGeo]
    slab: Optional[object] = None       # shapely polygon (with stair holes) -- set after all floors are known


@dataclass
class Analysis:
    building: Building
    floors: List[FloorGeo] = field(default_factory=list)

    @property
    def site(self):
        b = self.building
        return box(0, 0, b.width, b.depth) if finite(b.width, b.depth) and b.width > 0 and b.depth > 0 else None

    def floor_geo(self, floor_id: str) -> Optional[FloorGeo]:
        return next((f for f in self.floors if f.floor.id == floor_id), None)


def analyze(model) -> Analysis:
    b = model if isinstance(model, Building) else Building.from_dict(model)
    an = Analysis(building=b)
    t_ext = b.wall_exterior if finite(b.wall_exterior) else 0.0
    t_int = b.wall_interior if finite(b.wall_interior) else 0.0
    for fl in b.floors:
        # duplicate ids: keep the first occurrence for lookups (validator reports the rest)
        rooms: Dict[str, object] = {}
        for r in fl.rooms:
            rooms.setdefault(r.id, r)
        boxes = {rid: room_box(r) for rid, r in rooms.items() if room_has_geometry(r)}
        walls = derive_walls(fl.id, list(rooms.values()), t_ext, t_int)
        openings = resolve_openings(fl, rooms, boxes, walls, t_ext, t_int)
        stairs = {s.id: stair_geometry(s, fl.height) for s in fl.stairs}
        an.floors.append(FloorGeo(fl, rooms, boxes, walls, openings, stairs))
    # slabs: stairs of the floor below open the slab above
    for i, fg in enumerate(an.floors):
        holes = []
        if i > 0:
            below = an.floors[i - 1]
            holes = [g.footprint for g in below.stairs.values() if g.footprint]
        fg.slab = slab_polygon(list(fg.rooms.values()), holes)
    return an
