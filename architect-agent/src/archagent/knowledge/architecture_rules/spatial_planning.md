# Spatial planning

HARD RULES
* Every room lies fully inside the plot, inside the setback line, and inside the declared building region: `x>=setback`, `y>=setback`, `x+width<=site.width-setback`, `y+depth<=site.depth-setback`.
* Rooms never overlap (touching edges is fine and intended).
* Room ids/names are unique per building.
* Every dimension is positive, finite and in metres (or an explicit unit string such as `"60ft"`).

HEURISTICS
* Plan on a simple grid: bands of rooms along a corridor or hall; shared walls save area.
* Keep the footprint compact. Corners and notches make walls, cost and daylight problems.
* Public zone (living, dining, kitchen) near the entrance; private zone (bedrooms) away from it.
* Leave the front/driveway side for parking; put parking so a car can reach it from the plot edge.
* Plan circulation first (corridor / hall), then fill bands with rooms, then add doors.
* Reserve about 15-20 % of floor area for circulation and walls.
* Multi-floor: stack wet rooms (kitchen, bathrooms) above each other when possible.
