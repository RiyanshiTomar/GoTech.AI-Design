# Room adjacency

HEURISTICS (warnings only)
* Kitchen opens to dining or living (warning KITCHEN_ADJACENCY).
* Attach a bathroom to the master bedroom; keep at least one bathroom reachable from the corridor.
* Bathrooms should not open directly into the kitchen.
* Bedrooms open to a corridor or hall, not through another bedroom.
* Dining sits between kitchen and living.
* Utility/store next to the kitchen. Pooja room off the living area.
* Stair hall adjacent to entrance/living on the ground floor and to the corridor upstairs.

HARD RULES
* `connect(a, b)` requires that a and b share a wall (otherwise CONNECT_NO_SHARED_WALL).
* Adjacency alone is not access: rooms need doors to be reachable (see circulation).
