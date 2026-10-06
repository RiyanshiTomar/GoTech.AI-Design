"""Length parsing. Everything inside the model is stored in metres."""
from __future__ import annotations

import math
import re

UNIT_TO_M = {"m": 1.0, "cm": 0.01, "mm": 0.001, "ft": 0.3048, "in": 0.0254}
_LEN_RE = re.compile(r"^\s*(-?\d+(?:\.\d+)?)\s*([a-zA-Z\"']*)\s*$")
_ALIASES = {"meter": "m", "meters": "m", "metre": "m", "metres": "m", "feet": "ft", "foot": "ft",
            "'": "ft", '"': "in", "inch": "in", "inches": "in", "": None}


class UnitError(ValueError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


def normalize_unit(unit) -> str:
    u = str(unit).strip().lower() if unit is not None else "m"
    u = _ALIASES.get(u, u) or "m"
    if u not in UNIT_TO_M:
        raise UnitError("INVALID_UNIT", f"Unknown unit '{unit}'. Allowed: {', '.join(UNIT_TO_M)}.")
    return u


def to_meters(value, default_unit: str = "m") -> float:
    """Convert a number (in default_unit) or a string like '10ft' / '300 cm' to metres.

    Raises UnitError for malformed input. NaN/inf are rejected here.
    """
    if isinstance(value, bool) or value is None:
        raise UnitError("INVALID_VALUE", f"Expected a length, got {value!r}.")
    if isinstance(value, (int, float)):
        v = float(value)
        if math.isnan(v) or math.isinf(v):
            raise UnitError("INVALID_VALUE", f"Length is not a finite number: {value!r}.")
        return v * UNIT_TO_M[default_unit]
    if isinstance(value, str):
        m = _LEN_RE.match(value)
        if not m:
            raise UnitError("INVALID_VALUE", f"Cannot read length {value!r}. Use a number or e.g. '10ft', '3 m'.")
        num, unit = m.groups()
        u = normalize_unit(unit) if unit else default_unit
        return float(num) * UNIT_TO_M[u]
    raise UnitError("INVALID_VALUE", f"Cannot read length {value!r} (type {type(value).__name__}).")
