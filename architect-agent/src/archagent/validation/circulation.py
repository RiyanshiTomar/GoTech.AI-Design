"""Accessibility: every room must be reachable from an entrance, floors must connect."""
from __future__ import annotations

from collections import deque

from ..geometry.common import finite
from .issues import error
from .stairs import containing_room

OUTSIDE = "__outside__"


def validate_circulation(an):
    out = []
    floors = an.floors
    if not floors:
        return out
    graph = {}

    def node(fid, rid):
        return (fid, rid)

    def link(a, b):
        graph.setdefault(a, set()).add(b)
        graph.setdefault(b, set()).add(a)

    entrances = 0
    for idx, fg in enumerate(floors):
        fl = fg.floor
        for rid, room in fg.rooms.items():
            graph.setdefault(node(fl.id, rid), set())
            if room.is_open and idx == 0:
                link(node(fl.id, rid), OUTSIDE)           # ground-level open space == outside
        for op in fg.openings:
            if op.kind != "door" or op.problems:
                continue
            a = node(fl.id, op.room)
            if op.connects is not None:
                link(a, node(fl.id, op.connects))
            elif idx == 0:
                link(a, OUTSIDE)
                entrances += 1
            else:
                room = fg.rooms[op.room]
                out.append(error("DOOR_TO_VOID", [f"door '{op.id}' ({room.name})"],
                                 f"Door '{op.id}' of {room.name} on {fl.name} opens to nothing (there is no floor outside it).",
                                 hint="Open it into a balcony/terrace room, or remove it."))
        if idx == 0:
            entrances += sum(1 for op in fg.openings if op.kind == "door" and not op.problems and op.connects is not None and fg.rooms[op.connects].is_open)
    if entrances == 0:
        out.append(error("NO_ENTRANCE", [floors[0].floor.name], "The ground floor has no entrance. Add a door on an exterior wall of a ground-floor room (add_door(..., entrance=True)) or a door into a porch/parking.",
                         hint="Every building needs at least one door from outside."))
    # stairs link floors
    for i, fg in enumerate(floors[:-1]):
        up = floors[i + 1]
        for st in fg.floor.stairs:
            g = fg.stairs[st.id]
            if not g.ok or g.footprint is None:
                continue
            low = containing_room(fg, g.footprint)
            high = containing_room(up, g.footprint)
            if low is not None and high is not None:
                link(node(fg.floor.id, low.id), node(up.floor.id, high.id))
    # BFS from outside
    seen = {OUTSIDE}
    dq = deque([OUTSIDE])
    while dq:
        cur = dq.popleft()
        for nxt in graph.get(cur, ()):
            if nxt not in seen:
                seen.add(nxt)
                dq.append(nxt)
    for idx, fg in enumerate(floors):
        fl = fg.floor
        reachable_any = any(node(fl.id, rid) in seen for rid in fg.rooms)
        if idx > 0 and fg.rooms and not reachable_any:
            out.append(error("FLOOR_NOT_CONNECTED", [fl.name], f"{fl.name} cannot be reached from the entrance: no stair connects it to the floor below.",
                             hint=f"Add a stair on {floors[idx - 1].floor.name} whose footprint is inside rooms on both floors."))
            continue
        for rid, room in fg.rooms.items():
            if room.is_open and idx == 0:
                continue
            if node(fl.id, rid) in seen:
                continue
            if room.is_open:
                out.append(error("BALCONY_UNREACHABLE", [room.name], f"{room.name} on {fl.name} has no door from any room.", hint="Add a door from an adjacent room."))
            else:
                out.append(error("ROOM_UNREACHABLE", [room.name], f"{room.name} on {fl.name} cannot be reached: no door path leads to it from an entrance.",
                                 hint="Connect it with connect()/add_door() to a corridor or room that is reachable."))
    return out
