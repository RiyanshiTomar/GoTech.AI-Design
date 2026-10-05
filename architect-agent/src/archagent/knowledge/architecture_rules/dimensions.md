# Dimensions

HARD RULES (validator limits, shortest side of a room, metres)
bedroom 2.4 | living 2.7 | dining 2.1 | kitchen 1.8 | bathroom 1.2 | corridor 0.9 | parking 2.4 | study 1.8 | utility 0.9 | other 1.2.
Plot 3 m - 500 m per side. Floor height 2.4 - 6 m. Max 4 floors, default limit 2 unless the user asks for more.

TYPICAL TARGETS (heuristic)
* Master bedroom 3.6 x 4.2 m or larger; other bedrooms about 3.0 x 3.6 m.
* Living 3.6 x 5 m or larger; kitchen 2.4 x 3 m or larger; bathroom 1.5 x 2.4 m.
* One car: 2.7 x 5.5 m. Two cars: 5.4 x 5.5 m.
* Corridor at least 1.0 m clear between wall faces (1.2 m preferred).
* Floor height 3.0 m residential default.
* Wall thickness: exterior 0.23 m, interior 0.115 m (defaults; change via Building(...)).
* Room dimensions are wall-centreline-to-centreline footprints; exterior walls are laid inward, so interiors are slightly smaller.

IMPOSSIBLE BRIEFS
Declare the brief with `building.declare_program(bedroom=30, ...)`. If the minimum areas exceed what the plot can hold over the allowed floors, the validator answers PROGRAM_INFEASIBLE. Do not shrink rooms below the limits or place rooms outside the plot - explain the conflict and propose alternatives.
