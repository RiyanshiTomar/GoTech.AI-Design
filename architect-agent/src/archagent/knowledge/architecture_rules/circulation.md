# Circulation

HARD RULES
* There is at least one entrance door: `add_door(room, side, offset, entrance=True)` on an exterior wall of a ground-floor room.
* Every enclosed room can be reached from outside through doors (graph search from the entrance). Otherwise ROOM_UNREACHABLE.
* A door must open onto another room or outside, not onto empty void (DOOR_TO_VOID).
* Each upper floor is reachable through a stair from the floor below (FLOOR_NOT_CONNECTED).
* Balconies/terraces are reached from an inside room via a door (BALCONY_UNREACHABLE).

HEURISTICS
* Corridors are at least 1.0 m wide; avoid long dead-end corridors.
* No bedroom is a walk-through to other rooms (except attached bathrooms).
* Entrance opens to living/foyer, not to a bedroom or bathroom.
* Keep door-to-door paths short; place doors away from furniture walls (0.3 m+ from corners).
