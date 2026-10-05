# Walls

Walls are DERIVED, never authored. The agent must not draw walls.

* Each room edge becomes a wall. Edge shared by two enclosed rooms -> interior wall (centred on the edge). Edge with enclosed space on one side only -> exterior wall (thickness laid inward, so the outer face is on the room boundary).
* Open kinds (`parking, balcony, terrace, garden, porch`) have no walls.
* HARD: wall thickness must be within 0.05-0.6 m (exterior), 0.04-0.4 m (interior), and thin enough that a room keeps a positive interior (WALL_THICKNESS_TOO_LARGE / WALL_THICKNESS_INVALID).
* HARD: derived wall polygons must be valid rectangles (WALL_INVALID_POLYGON). Unusual notches can cause this; simplify the footprint.
* Keep rooms on a common grid so walls are continuous and corners are clean.
