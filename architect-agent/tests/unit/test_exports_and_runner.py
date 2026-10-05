import json
import os
from pathlib import Path

import ifcopenshell
import ifcopenshell.geom
import pytest
import trimesh

from archagent.agent.runner import run_design, run_workspace
from archagent.export import pipeline
from tests.support.scenarios import fixture_text


def build(tmp_path, source):
    (tmp_path / "design.py").write_text(source, encoding="utf-8")
    return run_workspace(str(tmp_path))


def test_valid_design_produces_all_artifacts(tmp_path):
    ok, text, status = build(tmp_path, fixture_text("house_3bhk_20x30"))
    assert ok and status["valid"] and not status["stale"]
    for rel in [*status["artifacts"]["svg"], status["artifacts"]["ifc"], status["artifacts"]["glb"]]:
        assert (tmp_path / "out" / rel).stat().st_size > 500
    assert json.loads((tmp_path / "out" / "model.json").read_text())["site"]["width"] == 20


def test_invalid_design_renders_nothing_and_exits_nonzero(tmp_path):
    bad = fixture_text("house_3bhk_20x30").replace('g.add_room("Bedroom 3", 14, 9, 5, 7)', 'g.add_room("Bedroom 3", 14, 9, 9, 7)')
    ok, text, status = build(tmp_path, bad)
    assert not ok and "VALIDATION FAILED" in text
    assert status["artifacts"] == {} and not (tmp_path / "out" / "artifacts" / "building.ifc").exists()


def test_failed_edit_keeps_last_valid_artifacts_but_flags_them_stale(tmp_path):
    build(tmp_path, fixture_text("house_3bhk_20x30"))
    ok, _, status = build(tmp_path, "building = None\n")
    assert not ok and status["stale"] and status["artifacts"].get("ifc")


def test_svg_has_meaningful_ids_and_one_file_per_floor(tmp_path):
    ok, _, status = build(tmp_path, fixture_text("small_house") + "\n" + fixture_text("first_floor_addition"))
    assert ok, _
    assert len(status["artifacts"]["svg"]) == 2
    svg = (tmp_path / "out" / status["artifacts"]["svg"][0]).read_text()
    for needle in ['id="room-living-room"', 'id="site-boundary"', 'id="walls"', 'id="door-', 'id="window-', 'id="stair-']:
        assert needle in svg, needle
    assert "<svg" in svg and "<image" not in svg           # vector, never a bitmap


def test_svg_is_deterministic(tmp_path):
    a = build(tmp_path, fixture_text("house_3bhk_20x30"))[2]
    first = (tmp_path / "out" / a["artifacts"]["svg"][0]).read_text()
    build(tmp_path, fixture_text("house_3bhk_20x30"))
    assert first == (tmp_path / "out" / a["artifacts"]["svg"][0]).read_text()


def test_ifc_contains_required_entities_and_real_geometry(tmp_path):
    ok, _, status = build(tmp_path, fixture_text("small_house") + "\n" + fixture_text("first_floor_addition"))
    f = ifcopenshell.open(str(tmp_path / "out" / status["artifacts"]["ifc"]))
    counts = {c: len(f.by_type(c)) for c in ["IfcProject", "IfcSite", "IfcBuilding", "IfcBuildingStorey", "IfcSpace", "IfcWall",
                                            "IfcDoor", "IfcWindow", "IfcSlab", "IfcStair"]}
    assert all(v >= 1 for v in counts.values()), counts
    assert counts["IfcBuildingStorey"] == 2
    settings = ifcopenshell.geom.settings()
    settings.set("use-world-coords", True)
    for el in f.by_type("IfcProduct"):
        if el.Representation is not None:
            assert len(ifcopenshell.geom.create_shape(settings, el).geometry.verts) > 0, el.Name
    assert all(len(w.HasOpenings) >= 0 for w in f.by_type("IfcWall"))
    assert any(w.HasOpenings for w in f.by_type("IfcWall"))      # doors/windows really cut the walls


def test_glb_is_valid_and_has_a_node_per_floor(tmp_path):
    ok, _, status = build(tmp_path, fixture_text("small_house") + "\n" + fixture_text("first_floor_addition"))
    scene = trimesh.load(str(tmp_path / "out" / status["artifacts"]["glb"]))
    names = set(scene.graph.nodes)
    assert {"floor-ground-floor", "floor-first-floor"} <= names
    (minx, miny, minz), (maxx, maxy, maxz) = scene.bounds
    assert 5.5 < maxy - miny + 0.2 < 7.0                   # two 3 m storeys plus the slab
    assert maxx - minx < 12.1 and maxz - minz < 14.1       # stays inside the plot (x east, -z north)


# ---- failure handling -----------------------------------------------------------------------------------------
@pytest.mark.parametrize("source,code", [
    ("", "DESIGN_EMPTY"),
    ("building = Building(width=10,", "PYTHON_SYNTAX_ERROR"),                          # partial LLM output
    ("from archagent import Building\nbuilding = Building(width=10, depth=10)\nbuilding.add_wall()", "PYTHON_RUNTIME_ERROR"),
    ("x = 1", "NO_BUILDING"),
    ("from archagent import Building\nbuilding = None", "NO_DESIGN_YET"),
    ("<<<<<<< SEARCH\nfoo\n=======", "PYTHON_SYNTAX_ERROR"),
])
def test_bad_llm_python_gives_structured_error(tmp_path, source, code):
    p = tmp_path / "design.py"
    p.write_text(source)
    b, err = run_design(str(p))
    assert b is None and err.code == code
    ok, text, status = build(tmp_path, source)
    assert not ok and code in text


@pytest.mark.parametrize("which", ["svg", "ifc", "glb"])
def test_exporter_exception_is_reported_not_swallowed(tmp_path, monkeypatch, which):
    def boom(*a, **k):
        raise RuntimeError("renderer exploded")
    monkeypatch.setattr(pipeline, {"svg": "render_all_svgs", "ifc": "export_ifc", "glb": "export_glb"}[which], boom)
    ok, text, status = build(tmp_path, fixture_text("house_3bhk_20x30"))
    assert not ok and status["valid"] is False and status["stale"]
    assert status["export_errors"][0]["code"] == f"{which.upper()}_EXPORT_FAILED"
    assert "EXPORT FAILED" in text


def test_infinite_loop_free_huge_input_is_rejected(tmp_path):
    ok, text, _ = build(tmp_path, "x = 1\n" * 200_000)
    assert not ok and "DESIGN_TOO_LARGE" in text
