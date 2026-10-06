"""Brief feasibility: can the declared programme fit this plot at all?"""
from __future__ import annotations

from collections import Counter

from ..geometry.common import finite
from . import rules
from .issues import error


def validate_program(an):
    b = an.building
    if not b.program:
        return []
    out = []
    if finite(b.width, b.depth, b.setback) and b.width - 2 * b.setback > 0 and b.depth - 2 * b.setback > 0:
        usable = (b.width - 2 * b.setback) * (b.depth - 2 * b.setback)
        floors_allowed = max(1, min(b.max_floors, rules.MAX_FLOORS_HARD))
        capacity = usable * rules.CIRCULATION_FACTOR * floors_allowed
        need = 0.0
        for kind, n in b.program.items():
            need += n * rules.MIN_AREA.get(kind, rules.MIN_AREA["default"])
        if need > capacity:
            per_floor = usable * rules.CIRCULATION_FACTOR
            floors_needed = -(-need // per_floor)
            out.append(error("PROGRAM_INFEASIBLE", ["brief"],
                             f"The declared programme needs about {need:.0f} m2 of rooms at minimum sizes, but the plot ({b.width:g} x {b.depth:g} m"
                             f"{', %g m setback' % b.setback if b.setback else ''}) offers about {capacity:.0f} m2 over {floors_allowed} floor(s). "
                             f"It would need ~{int(floors_needed)} floors on this plot.",
                             hint="Do not squeeze rooms outside the plot. Explain the conflict to the user and offer: fewer rooms, a bigger plot, or more floors.",
                             data={"required_m2": round(need, 1), "capacity_m2": round(capacity, 1), "floors_allowed": floors_allowed}))
            return out
    counts = Counter(r.kind for fg in an.floors for r in fg.rooms.values())
    for kind, n in b.program.items():
        if counts.get(kind, 0) < n:
            out.append(error("PROGRAM_MISMATCH", [kind], f"The declared programme has {n} x {kind} but the design contains {counts.get(kind, 0)}.",
                             hint="Add the missing rooms or update declare_program() to match the brief."))
    return out
