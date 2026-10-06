# Geometry rules (model conventions)

HARD RULES (validated)

* Units: metres. Plan axes: x = east (right), y = north (up). Origin = south-west corner of the plot. Floors stack in +z.
* Rooms are axis-aligned rectangles `(x, y, width, depth)` at the south-west corner. No rotation, no polygons in the PoC.
* Rooms of one floor are packed with touching edges; gaps become exterior voids and create extra exterior walls.
* A floor above must be supported by the floor below (UPPER_ROOM_UNSUPPORTED); balcony/terrace exempt.
* Never use NaN, infinity, negative or zero sizes. Never mix units silently - use explicit unit strings.

HEURISTICS (editing discipline)
* Preserve ids. Rename a room by editing its `name` only if the user asks; ids stay stable so doors and windows keep working.
* Make edits minimal: change one room's x/y/width/depth; shift neighbours by the same amount if the layout is packed; do not regenerate unrelated rooms.
* Invalid modification examples to refuse/explain: enlarging a room beyond the plot, two requests that move the same room to different places, resizing below a minimum dimension.
