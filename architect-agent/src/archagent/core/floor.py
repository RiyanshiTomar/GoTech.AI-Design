"""Floor: holds rooms/doors/windows/stairs and the authoring API on them."""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .entities import Door, Room, Stair, Window
from .naming import infer_kind, slugify


def shared_edge(a: Room, b: Room):
    """Return (side_of_a, lo, hi) for the wall interval shared by a and b, else None."""
    tol = 1e-6
    ax0, ay0, ax1, ay1 = a.bounds()
    bx0, by0, bx1, by1 = b.bounds()
    cands = []
    if abs(ay0 - by1) < tol:
        cands.append(("south", max(ax0, bx0), min(ax1, bx1)))
    if abs(ay1 - by0) < tol:
        cands.append(("north", max(ax0, bx0), min(ax1, bx1)))
    if abs(ax0 - bx1) < tol:
        cands.append(("west", max(ay0, by0), min(ay1, by1)))
    if abs(ax1 - bx0) < tol:
        cands.append(("east", max(ay0, by0), min(ay1, by1)))
    cands = [c for c in cands if c[2] - c[1] > tol]
    return max(cands, key=lambda c: c[2] - c[1]) if cands else None


@dataclass
class Floor:
    id: str
    name: str
    elevation: float
    height: float
    rooms: List[Room] = field(default_factory=list)
    doors: List[Door] = field(default_factory=list)
    windows: List[Window] = field(default_factory=list)
    stairs: List[Stair] = field(default_factory=list)
    _building: Any = field(default=None, repr=False, compare=False)

    # ------------------------------------------------------------------ helpers
    def _L(self, value, what):
        return self._building._len(value, f"{self.id}.{what}")

    def _issue(self, code, objects, details):
        self._building._issue(code, objects, details)

    @staticmethod
    def _unique(prefix: str, taken: List[str]) -> str:
        base = slugify(prefix)
        if base not in taken:
            return base
        n = 2
        while f"{base}-{n}" in taken:
            n += 1
        return f"{base}-{n}"

    def room_id(self, ref) -> str:
        """Accept a Room, an id, or a name (case-insensitive)."""
        if isinstance(ref, Room):
            return ref.id
        ref_s = str(ref)
        for r in self.rooms:
            if r.id == ref_s:
                return r.id
        for r in self.rooms:
            if r.name.lower() == ref_s.lower() or r.id == slugify(ref_s):
                return r.id
        return ref_s  # unknown -> validator reports UNKNOWN_ROOM

    def get_room(self, ref) -> Optional[Room]:
        rid = self.room_id(ref)
        return next((r for r in self.rooms if r.id == rid), None)

    # ------------------------------------------------------------------ authoring API
    def add_room(self, name, x, y, width, depth, kind=None, id=None) -> Room:
        rid = id if id else self._unique(name, [r.id for r in self.rooms])
        room = Room(
            id=str(rid), name=str(name), kind=(kind or infer_kind(str(name))).lower(),
            x=self._L(x, f"{rid}.x"), y=self._L(y, f"{rid}.y"),
            width=self._L(width, f"{rid}.width"), depth=self._L(depth, f"{rid}.depth"),
        )
        self.rooms.append(room)
        return room

    def add_door(self, room, side, offset, width='0.9m', height='2.1m', entrance=False,
                 swing="in", hinge="left", open=False, id=None) -> Door:
        did = id if id else self._unique("door", [d.id for d in self.doors])
        door = Door(id=str(did), room=self.room_id(room), side=str(side).lower(),
                    offset=self._L(offset, f"{did}.offset"), width=self._L(width, f"{did}.width"),
                    height=self._L(height, f"{did}.height"), entrance=bool(entrance),
                    swing=swing, hinge=hinge, open=bool(open))
        self.doors.append(door)
        return door

    def add_opening(self, room, side, offset, width='1.5m', height='2.1m', id=None) -> Door:
        """An open archway / open-plan connection (door without a leaf)."""
        return self.add_door(room, side, offset, width=width, height=height, open=True,
                             id=id or self._unique("opening", [d.id for d in self.doors]))

    def connect(self, room_a, room_b, width='0.9m', offset=None, height='2.1m', open=False,
                swing="in", hinge="left", id=None) -> Optional[Door]:
        """Door in the wall shared by two rooms. Position is automatic unless ``offset``
        (measured from the start of the SHARED wall, in metres) is given."""
        a, b = self.get_room(room_a), self.get_room(room_b)
        if a is None or b is None:
            self._issue("UNKNOWN_ROOM", [str(room_a), str(room_b)],
                        f"connect(): room '{room_a if a is None else room_b}' does not exist on {self.name}.")
            return None
        w = self._L(width, "connect.width")
        found = shared_edge(a, b)
        if found is None or math.isnan(w):
            self._issue("CONNECT_NO_SHARED_WALL", [a.name, b.name],
                        f"{a.name} and {b.name} do not share a wall, so no door can connect them.")
            return None
        side, lo, hi = found
        edge_start = a.x if side in ("south", "north") else a.y
        off = (lo + hi) / 2 - w / 2 - edge_start if offset is None else (lo - edge_start) + self._L(offset, "connect.offset")
        did = id if id else self._unique(f"door-{a.id}-{b.id}", [d.id for d in self.doors])
        door = Door(id=str(did), room=a.id, side=side, offset=off, width=w,
                    height=self._L(height, f"{did}.height"), swing=swing, hinge=hinge,
                    open=bool(open), expect_connects=b.id)
        self.doors.append(door)
        return door

    def add_window(self, room, side, offset, width='1.2m', sill='0.9m', height='1.2m', id=None) -> Window:
        wid = id if id else self._unique("window", [w.id for w in self.windows])
        win = Window(id=str(wid), room=self.room_id(room), side=str(side).lower(),
                     offset=self._L(offset, f"{wid}.offset"), width=self._L(width, f"{wid}.width"),
                     sill=self._L(sill, f"{wid}.sill"), height=self._L(height, f"{wid}.height"))
        self.windows.append(win)
        return win

    def add_stair(self, x, y, width, depth, direction="north", shape="straight", id=None) -> Stair:
        sid = id if id else self._unique("stair", [s.id for s in self.stairs])
        st = Stair(id=str(sid), x=self._L(x, f"{sid}.x"), y=self._L(y, f"{sid}.y"),
                   width=self._L(width, f"{sid}.width"), depth=self._L(depth, f"{sid}.depth"),
                   direction=str(direction).lower(), shape=str(shape).lower())
        self.stairs.append(st)
        return st

    # ------------------------------------------------------------------ serialisation
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id, "name": self.name, "elevation": self.elevation, "height": self.height,
            "rooms": [r.__dict__.copy() for r in self.rooms],
            "doors": [d.__dict__.copy() for d in self.doors],
            "windows": [w.__dict__.copy() for w in self.windows],
            "stairs": [s.__dict__.copy() for s in self.stairs],
        }
