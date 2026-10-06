"""Plain data records of the architecture model (all lengths in metres)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

# Spaces that are not enclosed by walls (no walls, no door required).
OPEN_KINDS = {"parking", "balcony", "terrace", "garden", "porch"}
SIDES = ("south", "east", "north", "west")
DIRECTIONS = ("north", "south", "east", "west")
STAIR_SHAPES = ("straight", "u")


@dataclass
class Room:
    id: str
    name: str
    kind: str
    x: float
    y: float
    width: float
    depth: float

    @property
    def is_open(self) -> bool:
        return self.kind in OPEN_KINDS

    def bounds(self):
        return (self.x, self.y, self.x + self.width, self.y + self.depth)


@dataclass
class Door:
    id: str
    room: str
    side: str
    offset: float            # from the start (west/south end) of the room edge
    width: float
    height: float = 2.1
    entrance: bool = False
    swing: str = "in"        # "in" (into the room) or "out"
    hinge: str = "left"      # "left" or "right" looking into the room from the door
    open: bool = False       # True = open archway, no leaf
    expect_connects: Optional[str] = None  # set by Floor.connect()


@dataclass
class Window:
    id: str
    room: str
    side: str
    offset: float
    width: float
    sill: float = 0.9
    height: float = 1.2


@dataclass
class Stair:
    id: str
    x: float
    y: float
    width: float
    depth: float
    direction: str = "north"   # direction of ascent
    shape: str = "straight"    # "straight" or "u"
