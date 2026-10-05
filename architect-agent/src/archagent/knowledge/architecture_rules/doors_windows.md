# Doors and windows

SDK: `floor.add_door(room, side, offset, width=0.9, entrance=False)`, `floor.connect(a, b)` (preferred between rooms), `floor.add_opening(...)` (archway), `floor.add_window(room, side, offset, width=1.2, sill=0.9, height=1.2)`.
`side` is the side of THAT room: south (y small), north, west (x small), east. `offset` is metres from the start of that side (west->east for south/north, south->north for east/west).

HARD RULES
* Every door/window sits on a real wall of an enclosed room (DOOR_NOT_ON_WALL / WINDOW_NOT_ON_WALL).
* It fits within the room edge and the wall segment, at least ~0.3 m from corners and junctions (OPENING_OUT_OF_EDGE, OPENING_OUT_OF_WALL).
* Doors 0.6-3.0 m wide, windows 0.3-6 m wide (DOOR_TOO_WIDE / WINDOW_TOO_WIDE / DOOR_SIZE_INVALID / WINDOW_SIZE_INVALID).
* Openings on the same wall keep at least 0.1 m of solid wall between them (OPENING_OVERLAP).
* A door created by `connect(a, b)` must still join a and b after moves (DOOR_CONNECT_MISMATCH) - re-run connect after moving rooms.
* Moving or resizing a room invalidates doors/windows placed by absolute offset on it; re-check them.

HEURISTICS
* Door width 0.9 m (1.0-1.2 m for main entrance, 0.75 m bathrooms).
* HARD: windows only on exterior walls (WINDOW_NOT_EXTERIOR); the entrance door must also be on an exterior wall (ENTRANCE_NOT_EXTERIOR).
* HEURISTIC: at least one in every bedroom, living, dining, kitchen (NO_DAYLIGHT warning otherwise).
* Windows small (0.6 m) in bathrooms; high sill 0.9 m, kitchen sill 1.0 m.
* Avoid placing windows opposite each other only through a hallway; prefer cross ventilation on two sides.
