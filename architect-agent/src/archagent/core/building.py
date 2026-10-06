"""Building: root of the architecture model (the JSON source of truth)."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .entities import Door, Room, Stair, Window
from .floor import Floor
from .naming import slugify
from .units import UnitError, normalize_unit, to_meters

SCHEMA_VERSION = 1


class Building:
    """Building(width=20, depth=30)             # plot in metres
       Building(width="60ft", depth="100ft")    # explicit units also work
       Building(width=40, depth=60, unit="ft")  # everything in feet

    Records what the agent asked for and never raises on bad geometry; call
    ``validate()`` (or run the build pipeline) to get structured errors.
    """

    def __init__(self, width=None, depth=None, unit="m", setback=0.0, wall_exterior=0.23,
                 wall_interior=0.115, max_floors=2, name="Building"):
        self.issues: List[Dict[str, Any]] = []
        try:
            self.unit = normalize_unit(unit)
        except UnitError as e:
            self.unit = "m"
            self._issue(e.code, ["building"], e.message)
        self.name = name
        self.max_floors = int(max_floors) if isinstance(max_floors, (int, float)) and max_floors >= 1 else 2
        self.floors: List[Floor] = []
        self.program: Dict[str, int] = {}
        self.min_dims: Dict[str, float] = {}
        if width is None or depth is None:
            self._issue("MISSING_DIMENSIONS", ["site"],
                        "Plot width and depth are required: Building(width=..., depth=...).")
        self.width = self._len(width, "site.width") if width is not None else float("nan")
        self.depth = self._len(depth, "site.depth") if depth is not None else float("nan")
        self.setback = self._len(setback, "site.setback")
        self.wall_exterior = self._len(wall_exterior, "wall_exterior")
        self.wall_interior = self._len(wall_interior, "wall_interior")

    # ------------------------------------------------------------------ internals
    def _issue(self, code, objects, details):
        self.issues.append({"code": code, "objects": list(objects), "details": details})

    def _len(self, value, what) -> float:
        try:
            return to_meters(value, self.unit)
        except UnitError as e:
            self._issue(e.code, [what], f"{what}: {e.message}")
            return float("nan")

    # ------------------------------------------------------------------ authoring API
    def add_floor(self, name="Ground Floor", elevation=None, height=3.0, id=None) -> Floor:
        base = id if id else slugify(name)
        fid, n, taken = base, 2, [f.id for f in self.floors]
        while fid in taken:
            fid = f"{base}-{n}"
            n += 1
        h = self._len(height, f"{fid}.height")
        if elevation is None:
            elev = (self.floors[-1].elevation + self.floors[-1].height) if self.floors else 0.0
        else:
            elev = self._len(elevation, f"{fid}.elevation")
        floor = Floor(id=fid, name=str(name), elevation=elev, height=h)
        floor._building = self
        self.floors.append(floor)
        return floor

    def declare_program(self, **counts):
        """Declare the brief, e.g. declare_program(bedroom=3, bathroom=2, kitchen=1, parking=1).
        The validator checks the programme can physically fit the plot (PROGRAM_INFEASIBLE)."""
        for kind, n in counts.items():
            try:
                self.program[str(kind).lower()] = int(n)
            except (TypeError, ValueError):
                self._issue("INVALID_VALUE", ["program"], f"declare_program({kind}={n!r}) needs an integer.")

    def floor(self, ref) -> Optional[Floor]:
        for f in self.floors:
            if f.id == ref or f.name.lower() == str(ref).lower():
                return f
        return None

    # ------------------------------------------------------------------ convenience pipeline
    def validate(self):
        from ..validation import validate_building
        return validate_building(self.to_dict())

    def export_ifc(self, path):
        from ..export.ifc import export_ifc
        return export_ifc(self.to_dict(), path)

    def render_2d(self, path, floor=None):
        from ..export.svg import render_floor_svg
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(render_floor_svg(self.to_dict(), floor))
        return path

    def export_3d(self, path):
        from ..export.glb import export_glb
        return export_glb(self.to_dict(), path)

    # ------------------------------------------------------------------ (de)serialisation
    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema": SCHEMA_VERSION,
            "name": self.name,
            "unit": "m",
            "site": {"width": self.width, "depth": self.depth, "setback": self.setback},
            "walls": {"exterior": self.wall_exterior, "interior": self.wall_interior},
            "max_floors": self.max_floors,
            "program": dict(self.program),
            "min_dims": dict(self.min_dims),
            "floors": [f.to_dict() for f in self.floors],
            "sdk_issues": list(self.issues),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Building":
        """Load a model dict (lengths already in metres). Malformed input raises ValueError."""
        if not isinstance(data, dict):
            raise ValueError("Architecture model must be a JSON object.")

        def pick(klass, d):
            return klass(**{k: v for k, v in d.items() if k in klass.__dataclass_fields__})

        try:
            site = data["site"]
            b = cls(width=site["width"], depth=site["depth"], unit="m", setback=site.get("setback", 0.0),
                    wall_exterior=data.get("walls", {}).get("exterior", 0.23),
                    wall_interior=data.get("walls", {}).get("interior", 0.115),
                    max_floors=data.get("max_floors", 2), name=data.get("name", "Building"))
            b.program = dict(data.get("program", {}))
            b.min_dims = dict(data.get("min_dims", {}))
            for fd in data.get("floors", []):
                f = Floor(id=fd["id"], name=fd["name"], elevation=float(fd["elevation"]), height=float(fd["height"]))
                f._building = b
                f.rooms = [pick(Room, r) for r in fd.get("rooms", [])]
                f.doors = [pick(Door, d) for d in fd.get("doors", [])]
                f.windows = [pick(Window, w) for w in fd.get("windows", [])]
                f.stairs = [pick(Stair, s) for s in fd.get("stairs", [])]
                b.floors.append(f)
            b.issues = list(data.get("sdk_issues", []))
            return b
        except (KeyError, TypeError, ValueError) as e:
            raise ValueError(f"Malformed architecture model: {type(e).__name__}: {e}") from e
