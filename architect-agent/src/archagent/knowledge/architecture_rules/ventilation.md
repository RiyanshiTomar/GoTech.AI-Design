# Ventilation

HEURISTICS (warnings only)
* Every habitable room (bedroom, living, dining, kitchen, study) has a window on an exterior wall: NO_DAYLIGHT warns otherwise.
* Prefer windows on two different walls in large rooms (cross ventilation).
* Bathrooms and kitchens need an exterior window or an exhaust; place them on exterior walls where possible.
* Windows can only be placed on exterior walls (hard rule WINDOW_NOT_EXTERIOR) - a room with no exterior wall gets no window.
* Interior rooms with no exterior wall (stair hall, store) are acceptable but not for sleeping.
