"""Doors and windows."""
from __future__ import annotations

from collections import defaultdict

from ..geometry.common import finite
from . import rules
from .issues import error


def validate_openings(an):
    out = []
    for fg in an.floors:
        fl = fg.floor
        walls = {w.id: w for w in fg.walls}
        recs = {d.id: d for d in fl.doors}
        recs.update({w.id: w for w in fl.windows})
        by_wall = defaultdict(list)
        for op in fg.openings:
            room = fg.rooms.get(op.room)
            rname = room.name if room else op.room
            tag = f"{op.kind} '{op.id}' ({rname})"
            for p in op.problems:
                out.append(error(p["code"], [tag], p["details"]))
            if op.problems:
                continue
            rec = recs[op.id]
            if op.kind == "door":
                lo, hi = rules.DOOR_WIDTH
                if not lo <= rec.width <= hi:
                    out.append(error("DOOR_SIZE_INVALID", [tag], f"Door width {rec.width:g} m must be between {lo} and {hi} m."))
                lo, hi = rules.DOOR_HEIGHT
                if not (lo <= rec.height <= hi) or (finite(fl.height) and rec.height > fl.height - 0.1):
                    out.append(error("DOOR_SIZE_INVALID", [tag], f"Door height {rec.height:g} m must be between {lo} and {hi} m and below the ceiling ({fl.height:g} m)."))
                if rec.swing not in ("in", "out") or rec.hinge not in ("left", "right"):
                    out.append(error("INVALID_VALUE", [tag], "Door swing must be 'in'/'out' and hinge 'left'/'right'."))
                if rec.entrance and op.connects is not None and not fg.rooms[op.connects].is_open:
                    out.append(error("ENTRANCE_NOT_EXTERIOR", [tag], f"{tag} is marked entrance but opens into {fg.rooms[op.connects].name}, not outside.",
                                     hint="Put the entrance door on an exterior wall."))
                if rec.expect_connects and op.connects != rec.expect_connects:
                    other = fg.rooms[op.connects].name if op.connects else "the outside"
                    out.append(error("DOOR_CONNECT_MISMATCH", [tag], f"{tag} was meant to connect to '{rec.expect_connects}' but now opens to {other}; the rooms are no longer adjacent.",
                                     hint="Call connect() again after moving rooms (it is recomputed on each run) or keep the rooms touching."))
            else:
                lo, hi = rules.WINDOW_WIDTH
                if not lo <= rec.width <= hi:
                    out.append(error("WINDOW_SIZE_INVALID", [tag], f"Window width {rec.width:g} m must be between {lo} and {hi} m."))
                lo, hi = rules.WINDOW_HEIGHT
                if not (lo <= rec.height <= hi) or rec.sill < 0 or (finite(fl.height) and rec.sill + rec.height > fl.height - 0.2):
                    out.append(error("WINDOW_SIZE_INVALID", [tag], f"Window sill {rec.sill:g} m + height {rec.height:g} m must fit under the ceiling ({fl.height:g} m) with a 0.2 m head."))
                wall = walls.get(op.wall_id)
                if wall is not None and wall.kind != "exterior":
                    out.append(error("WINDOW_NOT_EXTERIOR", [tag], f"{tag} is on an interior wall; windows belong on exterior walls.",
                                     hint="Move it to a side of the room that faces outside."))
            by_wall[op.wall_id].append(op)
        for wid, ops in by_wall.items():
            ops = sorted(ops, key=lambda o: o.a0)
            for a, b in zip(ops, ops[1:]):
                if b.a0 < a.a1 + rules.OPENING_GAP - 1e-9:
                    # a door and a window may share a wall only if they don't collide
                    out.append(error("OPENING_OVERLAP", [f"{a.kind} '{a.id}'", f"{b.kind} '{b.id}'"],
                                     f"{a.kind} '{a.id}' ({a.a0:.2f}-{a.a1:.2f} m) and {b.kind} '{b.id}' ({b.a0:.2f}-{b.a1:.2f} m) collide on wall {wid}; "
                                     f"keep at least {rules.OPENING_GAP:g} m of solid wall between openings."))
    return out
