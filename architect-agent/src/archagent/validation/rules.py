"""Numeric limits used by the validator.

These are PoC *practical* limits that keep geometry buildable and the renderers
sane. They are NOT building-code citations; real bylaws are out of scope. A
Building can override minimum room sizes via ``building.min_dims``.
"""
MAX_SITE_M = 500.0
MIN_SITE_M = 3.0
MAX_FLOORS_HARD = 4
FLOOR_HEIGHT = (2.4, 6.0)
WALL_THICKNESS_EXT = (0.05, 0.6)
WALL_THICKNESS_INT = (0.04, 0.4)

# smallest side (m) of a room by kind
MIN_SIDE = {
    "default": 1.2, "bedroom": 2.4, "bathroom": 1.2, "kitchen": 1.8, "living": 2.7, "dining": 2.1,
    "corridor": 0.9, "parking": 2.4, "pooja": 0.9, "study": 1.8, "utility": 0.9, "stair": 0.9,
    "balcony": 0.9, "terrace": 0.9, "porch": 0.9, "garden": 1.0,
}

# smallest comfortable area (m2) per kind -- used only for programme feasibility
MIN_AREA = {
    "default": 6.0, "bedroom": 9.0, "bathroom": 3.0, "kitchen": 6.0, "living": 14.0, "dining": 8.0,
    "corridor": 3.0, "parking": 12.0, "pooja": 1.5, "study": 6.0, "utility": 2.0, "stair": 4.0,
    "balcony": 3.0, "terrace": 6.0, "porch": 3.0, "garden": 6.0,
}
CIRCULATION_FACTOR = 0.80   # share of floor area usable for programme rooms

DOOR_WIDTH = (0.6, 3.0)
DOOR_HEIGHT = (1.8, 3.0)
WINDOW_WIDTH = (0.3, 6.0)
WINDOW_HEIGHT = (0.3, 3.0)
OPENING_GAP = 0.10          # minimum solid wall between two openings
HABITABLE = {"bedroom", "living", "dining", "kitchen", "study"}
