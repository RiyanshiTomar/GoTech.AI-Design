"""Every corner case listed in the brief maps to a structured error, never to a crash or a silent pass."""
import math

import pytest

from archagent import Building
from archagent.validation import validate_building


def report(b):
    return validate_building(b.to_dict() if hasattr(b, "to_dict") else b).to_dict()


def codes(r, key="errors"):
    return {e["code"] for e in r[key]}


def valid_base():
    b = Building(width=12, depth=10, setback=0.5)
    g = b.add_floor("Ground Floor", height=3.0)
    g.add_room("Living", 0.5, 0.5, 6, 5)
    g.add_room("Bedroom 1", 6.5, 0.5, 5, 5)
    g.add_door("Living", "south", 2, width=1.0, entrance=True)
    g.connect("Living", "Bedroom 1")
    g.add_window("Living", "west", 1.5)
    g.add_window("Bedroom 1", "east", 1.5)
    return b, g


def test_baseline_is_valid():
    b, _ = valid_base()
    assert report(b)["valid"] is True


# ---- site / dimensions / units ---------------------------------------------------------------------
def test_missing_plot_dimensions():
    assert "MISSING_DIMENSIONS" in codes(report(Building()))


@pytest.mark.parametrize("w,d,code", [(0, 10, "NONPOSITIVE_DIMENSION"), (-5, 10, "NONPOSITIVE_DIMENSION"),
                                      (10_000, 10, "EXTREME_DIMENSION"), (float("nan"), 10, None), ("abc", 10, "INVALID_VALUE")])
def test_bad_plot_dimensions(w, d, code):
    b = Building(width=w, depth=d)
    r = report(b)
    assert r["valid"] is False
    if code:
        assert code in codes(r)


def test_invalid_unit_and_mixed_units():
    assert "INVALID_UNIT" in codes(report(Building(width=10, depth=10, unit="parsec")))
    b = Building(width="60ft", depth=40, unit="ft")          # explicit unit string mixed with a default unit is converted
    assert math.isclose(b.width, 60 * 0.3048)
    assert math.isclose(b.depth, 40 * 0.3048)


def test_malformed_model_json():
    for bad in ({}, {"site": {}}, {"site": {"width": 1}}, [], "x", {"site": {"width": 10, "depth": 10}, "floors": [{"id": "g"}]}):
        r = validate_building(bad).to_dict()
        assert r["valid"] is False and "MALFORMED_MODEL" in codes(r)


# ---- rooms ------------------------------------------------------------------------------------------
def test_room_outside_site_and_building_boundary():
    b, g = valid_base()
    g.add_room("Study", 10, 8, 3, 3)                      # crosses east and north limits
    r = report(b)
    assert {"OUT_OF_BOUNDS", "ROOM_OUTSIDE_SITE"} & codes(r)
    far = Building(width=12, depth=10, setback=0.5)
    f = far.add_floor("G")
    f.add_room("Far", 20, 20, 3, 3)
    assert "ROOM_OUTSIDE_SITE" in codes(report(far))


def test_zero_negative_dimension_rooms():
    b, g = valid_base()
    g.add_room("Zero", 1, 6, 0, 3)
    g.add_room("Neg", 3, 6, -2, 3)
    assert {"ZERO_DIMENSION", "NEGATIVE_DIMENSION"} <= codes(report(b))


def test_overlap_reports_area_and_both_rooms():
    b, g = valid_base()
    g.add_room("Study", 5, 3, 3, 3)
    e = next(e for e in report(b)["errors"] if e["code"] == "ROOM_OVERLAP")
    assert "square metres" in e["details"] and len(e["objects"]) == 2


def test_duplicate_ids():
    b, g = valid_base()
    from archagent.core.entities import Room
    g.rooms.append(Room(id=g.rooms[0].id, name="Copy", kind="room", x=7, y=6, width=3, depth=3))
    assert "DUPLICATE_ID" in codes(report(b))


def test_minimum_dimensions_and_narrow_corridor():
    b, g = valid_base()
    g.add_room("Closet Bedroom", 0.5, 5.5, 1.0, 3)        # bedroom narrower than 2.4 m
    g.add_room("Hall", 1.5, 5.5, 0.6, 3, kind="corridor")
    c = codes(report(b))
    assert "MIN_DIMENSION" in c and "CORRIDOR_TOO_NARROW" in c


def test_wall_too_thick():
    b = Building(width=10, depth=10, wall_exterior=2.5, wall_interior=0.1)
    g = b.add_floor("G")
    g.add_room("Living", 0, 0, 4, 4)
    assert codes(report(b)) & {"WALL_THICKNESS_TOO_LARGE", "WALL_THICKNESS_INVALID"}


# ---- circulation ---------------------------------------------------------------------------------------
def test_disconnected_room_has_no_access():
    b, g = valid_base()
    g.add_room("Store", 0.5, 5.5, 3, 3)
    r = report(b)
    assert any(e["code"] == "ROOM_UNREACHABLE" and "Store" in e["objects"] for e in r["errors"])


def test_no_entrance():
    b = Building(width=10, depth=10)
    g = b.add_floor("G")
    g.add_room("Living", 0.5, 0.5, 5, 5)
    assert "NO_ENTRANCE" in codes(report(b))


# ---- doors / windows ----------------------------------------------------------------------------------------
def test_door_not_attached_to_a_wall_and_unknown_room():
    b, g = valid_base()
    g.add_door("Bedroom 1", "east", 20, width=1)
    g.add_door("Ghost Room", "south", 1)
    c = codes(report(b))
    assert "OPENING_OUT_OF_EDGE" in c and "UNKNOWN_ROOM" in c


def test_door_wider_than_wall():
    b, g = valid_base()
    g.add_door("Bedroom 1", "north", 0.1, width=4.9)
    assert codes(report(b)) & {"DOOR_TOO_WIDE", "OPENING_OUT_OF_WALL"}


def test_window_not_on_exterior_wall():
    b, g = valid_base()
    g.add_window("Living", "east", 2.0)                    # shared wall with Bedroom 1
    assert "WINDOW_NOT_EXTERIOR" in codes(report(b))


def test_overlapping_openings():
    b, g = valid_base()
    g.add_window("Living", "west", 1.6, width=1.2)         # overlaps window at 1.5-3.0
    assert "OPENING_OVERLAP" in codes(report(b))


def test_open_space_cannot_hold_door():
    b, g = valid_base()
    g.add_room("Parking", 0.5, 5.5, 5, 4, kind="parking")
    g.add_door("Parking", "south", 1)
    assert any(c.endswith("NOT_ON_WALL") for c in codes(report(b)))


# ---- stairs / floors ---------------------------------------------------------------------------------------------
def two_floor():
    b = Building(width=12, depth=10, setback=0.5)
    g = b.add_floor("Ground Floor", height=3.0)
    g.add_room("Hall", 0.5, 0.5, 6, 5)
    g.add_door("Hall", "south", 2, width=1.0, entrance=True)
    g.add_window("Hall", "west", 1.5)
    g.add_room("Dining", 6.5, 0.5, 5, 5)
    g.connect("Hall", "Dining")
    g.add_window("Dining", "east", 1.5)
    f = b.add_floor("First Floor", height=3.0)
    f.add_room("Landing", 0.5, 0.5, 6, 5, kind="corridor")
    f.add_room("Bedroom 2", 6.5, 0.5, 5, 5)
    f.connect("Landing", "Bedroom 2")
    f.add_window("Bedroom 2", "east", 1.5)
    return b, g, f


def test_floor_above_without_access():
    b, g, f = two_floor()
    r = report(b)
    assert "FLOOR_NOT_CONNECTED" in codes(r)


def test_valid_two_floors_with_stair():
    b, g, f = two_floor()
    g.add_stair(1.2, 0.8, 4.0, 1.0, "east")
    assert report(b)["valid"] is True


def test_stair_outside_building_and_not_in_room():
    b, g, f = two_floor()
    g.add_stair(50, 50, 4.0, 1.0, "east")
    assert codes(report(b)) & {"STAIR_OUT_OF_BOUNDS", "STAIR_NOT_IN_ROOM"}


def test_stair_too_short_for_height():
    b, g, f = two_floor()
    g.add_stair(1.2, 0.8, 2.0, 1.0, "east")
    assert codes(report(b)) & {"STAIR_GEOMETRY", "STAIR_RUN_TOO_SHORT", "STAIR_INVALID"} or any(
        e["code"].startswith("STAIR") for e in report(b)["errors"])


def test_stair_without_upper_floor_and_no_landing_above():
    b = Building(width=12, depth=10)
    g = b.add_floor("G")
    g.add_room("Hall", 0.5, 0.5, 6, 5)
    g.add_door("Hall", "south", 2, entrance=True)
    g.add_stair(1.2, 0.8, 4.0, 1.0, "east")
    assert "STAIR_NO_UPPER_FLOOR" in codes(report(b))


def test_incompatible_footprints_upper_room_unsupported():
    b, g, f = two_floor()
    f.add_room("Overhang", 0.5, 5.5, 5, 3)                # nothing below it
    assert "UPPER_ROOM_UNSUPPORTED" in codes(report(b))


def test_too_many_floors():
    b = Building(width=12, depth=10, max_floors=2)
    for i in range(6):
        b.add_floor(f"F{i}")
    assert "TOO_MANY_FLOORS" in codes(report(b))


# ---- impossible programme ---------------------------------------------------------------------------------------------
def test_impossible_programme_is_reported_not_forced():
    b = Building(width=10, depth=10, setback=0.5)
    b.declare_program(bedroom=30)
    b.add_floor("G").add_room("Bedroom 1", 0.5, 0.5, 5, 5)
    r = report(b)
    e = next(e for e in r["errors"] if e["code"] == "PROGRAM_INFEASIBLE")
    assert e["data"]["required_m2"] > e["data"]["capacity_m2"]


def test_warnings_do_not_invalidate():
    b, g = valid_base()
    g.add_room("Narrow Living", 0.5, 5.5, 11, 3)           # aspect ratio heuristic; no window -> NO_DAYLIGHT
    g.connect("Living", "Narrow Living")
    r = report(b)
    assert r["valid"] is True and r["warnings"]
