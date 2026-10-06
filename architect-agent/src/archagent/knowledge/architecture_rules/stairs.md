# Stairs

SDK: `floor.add_stair(x, y, width, depth, direction="north", shape="straight"|"u")`. The stair is placed on the LOWER floor; `direction` is the way you walk up. The slab above is cut automatically.

HARD RULES (PoC practical limits)
* Riser <= 0.19 m (step count is computed from floor height), tread >= 0.25 m, clear width >= 0.9 m.
* Straight run needs length >= (risers-1) x 0.25 m: about 3.9 m for a 3.0 m floor height (16 risers). A "u" stair needs about 2 x 0.9 m width and ~2.8 m length.
* The stair footprint lies completely inside ONE enclosed room (a stair hall/living) on the lower floor (STAIR_NOT_IN_ROOM / STAIR_OUT_OF_BOUNDS / STAIR_OVERLAP).
* The floor above has a room there (so the arrival is on a slab) with 1 m clear landing beyond the last step (STAIR_NO_LANDING_ABOVE).
* Stair exists only if there is a floor above (STAIR_NO_UPPER_FLOOR), and every upper floor must be connected by one (FLOOR_NOT_CONNECTED).

HEURISTICS
* Put the stair near the entrance/hall; keep 0.9 m clear approach before the first step (STAIR_ENTRY_TIGHT warning).
* Give the stair its own "Stair Hall" room (kind stair) at least 1.5 m x 4.5 m for a straight stair.
* Upstairs, open the stair into a landing/corridor room.
