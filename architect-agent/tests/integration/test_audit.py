"""Audit tests: one canonical model, identical dimensions in every output, units, hard failures A-J.
All offline, no LLM."""
import json
import re

import ifcopenshell
import ifcopenshell.geom
import numpy as np
import pytest
import trimesh

from archagent import Building
from archagent.agent.runner import run_workspace
from archagent.export.glb import export_glb
from archagent.export.ifc import export_ifc
from archagent.export.svg import SCALE, render_floor_svg
from archagent.geometry import analyze
from archagent.validation import validate_building
from tests.support.scenarios import fixture_text


def codes(rep, key="errors"):
    return {e["code"] for e in rep.to_dict()[key]}


def run(tmp_path, src):
    (tmp_path / "design.py").write_text(src)
    return run_workspace(str(tmp_path))


# ------------------------------------------------------------------ one geometry for every output
def test_bedroom_4_by_5_is_4_by_5_in_model_svg_ifc_and_glb(tmp_path):
    b = Building(width=15, depth=15)
    g = b.add_floor("Ground Floor", height=3.0)
    g.add_room("Bedroom 1", 2, 3, 4, 5)
    g.add_door("Bedroom 1", "south", 1.5, entrance=True)
    g.add_window("Bedroom 1", "west", 1.5)
    model = b.to_dict()
    assert validate_building(model).valid
    r = model["floors"][0]["rooms"][0]
    assert (r["x"], r["y"], r["width"], r["depth"]) == (2, 3, 4, 5)

    svg = render_floor_svg(model, "ground-floor")
    m = re.search(r'<g id="room-bedroom-1".*?<rect class="room"\s+x="([\d.]+)" y="([\d.]+)" width="([\d.]+)" height="([\d.]+)"', svg)
    assert float(m.group(3)) / SCALE == 4 and float(m.group(4)) / SCALE == 5

    export_ifc(model, str(tmp_path / "b.ifc"))
    f = ifcopenshell.open(str(tmp_path / "b.ifc"))
    s = ifcopenshell.geom.settings(); s.set("use-world-coords", True)
    sp = next(x for x in f.by_type("IfcSpace") if x.Name == "Bedroom 1")
    v = np.array(ifcopenshell.geom.create_shape(s, sp).geometry.verts).reshape(-1, 3)
    assert np.allclose(v.max(0) - v.min(0), [4, 5, 3], atol=1e-6) and np.allclose(v.min(0)[:2], [2, 3], atol=1e-6)

    export_glb(model, str(tmp_path / "b.glb"))
    sc = trimesh.load(str(tmp_path / "b.glb"))
    slab = sc.geometry["ground-floor-slab"].bounds              # glTF: x east, y up, z = -north (single conversion point)
    assert np.allclose([slab[1][0] - slab[0][0], slab[1][2] - slab[0][2]], [4, 5], atol=1e-6)
    assert np.allclose([slab[0][0], -slab[1][2]], [2, 3], atol=1e-6)


def test_ifc_is_in_metres_not_millimetres(tmp_path):
    b = Building(width=20, depth=30)
    g = b.add_floor("G"); g.add_room("Living", 0, 0, 20, 30); g.add_door("Living", "south", 5, entrance=True)
    export_ifc(b.to_dict(), str(tmp_path / "u.ifc"))
    import ifcopenshell.util.unit as U
    f = ifcopenshell.open(str(tmp_path / "u.ifc"))
    assert U.calculate_unit_scale(f) == 1.0
    assert "MILLI" not in {getattr(u, "Prefix", None) or "" for u in f.by_type("IfcSIUnit")}


def test_ifc_hierarchy_and_containment(tmp_path):
    ok, _, st = run(tmp_path, fixture_text("small_house") + "\n" + fixture_text("first_floor_addition"))
    f = ifcopenshell.open(str(tmp_path / "out" / st["artifacts"]["ifc"]))
    site = f.by_type("IfcSite")[0]; bld = f.by_type("IfcBuilding")[0]
    assert f.by_type("IfcProject")[0].IsDecomposedBy[0].RelatedObjects == (site,)
    assert site.IsDecomposedBy[0].RelatedObjects == (bld,)
    storeys = bld.IsDecomposedBy[0].RelatedObjects
    assert [round(s.Elevation, 3) for s in sorted(storeys, key=lambda s: s.Elevation)] == [0.0, 3.0]
    for w in f.by_type("IfcWall"):
        assert w.ContainedInStructure[0].RelatingStructure in storeys
    for sp in f.by_type("IfcSpace"):
        assert sp.Decomposes[0].RelatingObject in storeys
    assert all(d.FillsVoids for d in f.by_type("IfcDoor")) and all(d.FillsVoids for d in f.by_type("IfcWindow"))


def test_outputs_do_not_depend_on_chat_and_are_deterministic(tmp_path):
    src = fixture_text("house_3bhk_20x30")
    ok, _, a = run(tmp_path, src)
    first = {k: (tmp_path / "out" / v).read_bytes() for k, v in [("svg", a["artifacts"]["svg"][0]), ("glb", a["artifacts"]["glb"])]}
    run(tmp_path, src)
    assert first["svg"] == (tmp_path / "out" / a["artifacts"]["svg"][0]).read_bytes()
    assert first["glb"] == (tmp_path / "out" / a["artifacts"]["glb"]).read_bytes()


# ------------------------------------------------------------------ geometry conventions
def test_touching_edges_are_not_an_overlap_but_one_shared_wall():
    b = Building(width=20, depth=10)
    g = b.add_floor("G")
    g.add_room("A", 0, 0, 5, 5); g.add_room("B", 5, 0, 5, 5)
    g.add_door("A", "south", 1, entrance=True); g.connect("A", "B")
    assert "ROOM_OVERLAP" not in codes(validate_building(b.to_dict()))
    walls = analyze(b.to_dict()).floors[0].walls
    shared = [w for w in walls if w.kind == "interior"]
    assert len(shared) == 1                                   # one wall for the shared edge, not one per room
    total = sum((w.x1 - w.x0) * (w.y1 - w.y0) for w in walls)
    from shapely.geometry import box
    from shapely.ops import unary_union
    assert abs(unary_union([box(*w.rect) for w in walls]).area - total) < 1e-9          # no overlapping wall pieces


def test_exterior_walls_stay_inside_the_room_footprint_and_site():
    b = Building(width=10, depth=10, wall_exterior=0.3)
    g = b.add_floor("G"); g.add_room("A", 0, 0, 10, 10); g.add_door("A", "south", 4, entrance=True)
    for w in analyze(b.to_dict()).floors[0].walls:
        assert w.x0 >= 0 and w.y0 >= 0 and w.x1 <= 10 and w.y1 <= 10     # canonical convention: room box = outer face


def test_wall_ids_are_stable_when_unrelated_rooms_change():
    def ids(w):
        b = Building(width=20, depth=30); g = b.add_floor("G"); g.add_room("A", 0, 0, 4, 5); g.add_room("B", 4, 0, w, 5)
        return {x.id for x in analyze(b.to_dict()).floors[0].walls}
    a, b2 = ids(4), ids(5)
    assert {"g-wall-x0-0-400", "g-wall-y0-0-500"} <= a & b2


def test_issue_schema_is_machine_readable():
    b = Building(width=15, depth=15); g = b.add_floor("G"); g.add_room("Big Room", 0, 0, 16, 5)
    e = next(e for e in validate_building(b.to_dict()).to_dict()["errors"] if e["code"] == "ROOM_OUTSIDE_SITE")
    assert e["severity"] == "error" and e["object_ids"] == ["big-room"] and e["data"]["overshoot"] == {"east": 1.0}
    assert "east boundary by 1.00 m" in e["message"]


def test_warnings_and_errors_are_separate_severities():
    rep = validate_building(Building(width=10, depth=10).to_dict()).to_dict()
    assert all(x["severity"] == "error" for x in rep["errors"]) and all(x["severity"] == "warning" for x in rep["warnings"])


# ------------------------------------------------------------------ units
@pytest.mark.parametrize("w,d,unit", [(2000, 3000, "cm"), (20000, 30000, "mm"), ("20m", "30m", "m"), ("2000cm", "30000mm", "m")])
def test_inputs_normalise_to_metres(w, d, unit):
    b = Building(width=w, depth=d, unit=unit)
    assert (round(b.width, 6), round(b.depth, 6)) == (20.0, 30.0)


def test_feet_convert_correctly():
    assert abs(Building(width="65.6ft", depth=1).width - 19.99488) < 1e-6


def test_J_converting_all_dimensions_to_centimetres_gives_the_same_model():
    def build(unit, k):
        b = Building(width=20 * k, depth=30 * k, unit=unit, setback=1 * k, wall_exterior=0.23 * k, wall_interior=0.115 * k)
        g = b.add_floor("G", height=3 * k)
        g.add_room("Living", 1 * k, 1 * k, 6 * k, 5 * k); g.add_room("Kitchen", 7 * k, 1 * k, 4 * k, 4 * k)
        g.add_door("Living", "south", 2 * k, width=1 * k, entrance=True); g.connect("Living", "Kitchen")
        g.add_window("Living", "west", 1.5 * k)
        return b.to_dict()
    m, cm = build("m", 1), build("cm", 100)
    def norm(x):
        return json.loads(json.dumps(x), parse_float=lambda s: round(float(s), 6))
    assert norm(m) == norm(cm)


# ------------------------------------------------------------------ A-J
def test_A_room_wider_than_building():
    b = Building(width=10, depth=10); g = b.add_floor("G"); g.add_room("Hall", 0, 0, 15, 5)
    assert codes(validate_building(b.to_dict())) & {"ROOM_OUTSIDE_SITE", "OUT_OF_BOUNDS"}


def test_B_100_bedrooms_in_20x20(tmp_path):
    src = ('from archagent import Building\nbuilding = Building(width=20, depth=20)\nbuilding.declare_program(bedroom=100)\n'
           'g = building.add_floor("G")\ng.add_room("Bedroom 1", 0, 0, 4, 4)\ng.add_door("Bedroom 1", "south", 1, entrance=True)\n')
    ok, text, st = run(tmp_path, src)
    assert not ok and "PROGRAM_INFEASIBLE" in text and st["artifacts"] == {}


def test_C_negative_width():
    b = Building(width=10, depth=10); g = b.add_floor("G"); g.add_room("Bedroom 1", 0, 0, -4, 3)
    assert "NEGATIVE_DIMENSION" in codes(validate_building(b.to_dict()))


def test_D_move_bathroom_100m_east():
    src = fixture_text("small_house").replace('add_room("Bathroom 1", 0.5, 8.5, 3, 2.5)', 'add_room("Bathroom 1", 100.5, 8.5, 3, 2.5)')
    b = Building.from_dict(json.loads(json.dumps(_model(src))))
    assert "ROOM_OUTSIDE_SITE" in codes(validate_building(b))


def _model(src):
    import tempfile
    from archagent.agent.sandbox import run_design_file
    d = tempfile.mkdtemp(); (open(d + "/design.py", "w")).write(src)
    m, err = run_design_file(d + "/design.py"); assert err is None, err
    return m


def test_E_remove_every_door():
    src = "\n".join(l for l in fixture_text("small_house").splitlines() if "add_door" not in l and "connect(" not in l)
    c = codes(validate_building(_model(src)))
    assert "NO_ENTRANCE" in c and "ROOM_UNREACHABLE" in c


def test_F_5m_door_in_3m_wall():
    b = Building(width=10, depth=10); g = b.add_floor("G"); g.add_room("A", 0, 0, 3, 3)
    g.add_door("A", "south", 0, width=5, entrance=True)
    assert codes(validate_building(b.to_dict())) & {"DOOR_TOO_WIDE", "OPENING_OUT_OF_EDGE", "OPENING_OUT_OF_WALL"}


def test_G_another_floor_gets_correct_elevation_and_needs_a_stair():
    src = fixture_text("small_house") + "\n" + fixture_text("first_floor_addition")
    m = _model(src)
    assert [f["elevation"] for f in m["floors"]] == [0.0, 3.0]
    assert validate_building(m).valid
    no_stair = "\n".join(l for l in src.splitlines() if "add_stair" not in l)
    assert "FLOOR_NOT_CONNECTED" in codes(validate_building(_model(no_stair)))


def test_H_moving_bedroom_by_20cm_only_changes_what_is_necessary():
    base = fixture_text("small_house")
    naive = base.replace('add_room("Bedroom 1", 0.5, 5.5, 3, 3)', 'add_room("Bedroom 1", 0.7, 5.5, 3, 3)')
    assert "ROOM_OVERLAP" in codes(validate_building(_model(naive)))             # 20 cm into the Study: caught, not clipped
    fixed = naive.replace('add_room("Study", 3.5, 5.5, 4, 3)', 'add_room("Study", 3.7, 5.5, 3.8, 3)')
    m0, m1 = _model(base), _model(fixed)
    assert validate_building(m1).valid
    rooms0 = {r["id"]: r for r in m0["floors"][0]["rooms"]}; rooms1 = {r["id"]: r for r in m1["floors"][0]["rooms"]}
    assert {k for k in rooms0 if rooms0[k] != rooms1[k]} == {"bedroom-1", "study"}


def test_I_reducing_the_site_revalidates_everything():
    src = fixture_text("house_3bhk_20x30").replace("Building(width=20, depth=30", "Building(width=15, depth=20")
    rep = validate_building(_model(src))
    assert not rep.valid and {"OUT_OF_BOUNDS", "ROOM_OUTSIDE_SITE"} & codes(rep)
    assert len([e for e in rep.errors if e.code in ("OUT_OF_BOUNDS", "ROOM_OUTSIDE_SITE")]) >= 3


def test_malformed_and_unsupported_model_input_is_rejected():
    for bad in ({"site": {"width": "x", "depth": 3}, "floors": []}, {"site": {"width": 3, "depth": 3}, "floors": [{"id": "a"}]}):
        assert "MALFORMED_MODEL" in codes(validate_building(bad)) or not validate_building(bad).valid
