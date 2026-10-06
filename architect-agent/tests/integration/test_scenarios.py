"""The five required end-to-end scenarios. The Aider loop, the SDK, validator and exporters are all real;
only the LLM network call is replaced by a script."""
import json
import os

import ifcopenshell

from tests.conftest import codes, room_rects
from tests.support import scenarios as sc


def sent(messages, needle):
    """Was `needle` part of what the (fake) LLM received on that call?"""
    return any(needle in (m.get("content") or "") for m in messages if isinstance(m.get("content"), str))


def outdir(s):
    return os.path.join(s.workspace, "out")


def test_1_single_floor_3bhk(make_session):
    s = make_session([sc.REPLY_3BHK])
    r = s.chat(sc.PROMPT_3BHK)
    assert r.valid and not r.rolled_back
    st = s.state()
    assert st["status"]["valid"] and st["status"]["report"]["errors"] == []
    rooms = room_rects(st["model"], "ground-floor")
    kinds = [x["kind"] for x in st["model"]["floors"][0]["rooms"]]
    assert kinds.count("bedroom") == 3 and kinds.count("bathroom") == 2 and "kitchen" in kinds and "living" in kinds and "parking" in kinds
    # boundary + no overlap, re-checked independently of the validator
    for (x, y, w, d) in rooms.values():
        assert x >= 1 and y >= 1 and x + w <= 19 and y + d <= 29
    items = list(rooms.values())
    for i, a in enumerate(items):
        for b in items[i + 1:]:
            ox = min(a[0] + a[2], b[0] + b[2]) - max(a[0], b[0])
            oy = min(a[1] + a[3], b[1] + b[3]) - max(a[1], b[1])
            assert not (ox > 1e-9 and oy > 1e-9), (a, b)
    arts = st["status"]["artifacts"]
    assert os.path.getsize(os.path.join(outdir(s), arts["ifc"])) > 1000
    assert os.path.getsize(os.path.join(outdir(s), arts["glb"])) > 1000
    assert open(os.path.join(outdir(s), arts["svg"][0])).read().startswith("<svg")
    assert "Plot 20 x 30" in r.reply and "<<<<" not in r.reply        # reasoning shown, edit blocks hidden


def test_2_impossible_program_is_explained_and_nothing_invalid_is_kept(make_session):
    s = make_session([sc.REPLY_30_BEDROOMS_ATTEMPT, sc.REPLY_30_BEDROOMS_EXPLAIN])
    r = s.chat(sc.PROMPT_30_BEDROOMS)
    # validator rejected the attempt with the structured infeasibility error ...
    assert r.rolled_back and "PROGRAM_INFEASIBLE" in codes(r.rejected)
    # ... the LLM was shown that error and answered by explaining ...
    assert sent(s.coder.scripted_calls[1], "PROGRAM_INFEASIBLE")
    assert "cannot reasonably fit" in r.reply
    # ... and no invalid geometry was kept or rendered.
    assert "building = None" in s.state()["design"]
    assert s.state()["status"]["artifacts"] == {}
    assert not os.path.exists(os.path.join(outdir(s), "artifacts", "building.ifc"))


def test_3a_unrepairable_widening_is_rejected_and_previous_design_restored(make_session):
    base = sc.fixture_text("small_house")
    s = make_session([sc.REPLY_WIDEN_5_NAIVE, sc.REPLY_WIDEN_5_EXPLAIN], start_design=base)
    before = room_rects(s.state()["model"], "ground-floor")
    r = s.chat(sc.PROMPT_WIDEN_5)
    assert r.rolled_back
    assert {"ROOM_OVERLAP", "OUT_OF_BOUNDS"} & codes(r.rejected)
    assert sent(s.coder.scripted_calls[1], "VALIDATION FAILED") and sent(s.coder.scripted_calls[1], "ROOM_OVERLAP")
    assert s.state()["design"] == base                                    # design.py restored
    assert room_rects(s.state()["model"], "ground-floor") == before
    assert s.state()["status"]["valid"] is True


def test_3b_repairable_widening_is_fixed_through_the_validation_loop(make_session):
    base = sc.fixture_text("small_house")
    s = make_session([sc.REPLY_WIDEN_1_NAIVE, sc.REPLY_WIDEN_1_REPAIR], start_design=base)
    before = room_rects(s.state()["model"], "ground-floor")
    r = s.chat(sc.PROMPT_WIDEN_1)
    assert r.valid and not r.rolled_back
    assert sent(s.coder.scripted_calls[1], "ROOM_OVERLAP")      # first attempt failed, error was fed back
    after = room_rects(s.state()["model"], "ground-floor")
    assert after["bedroom-1"][2] == 4 and after["study"][2] == 3
    unchanged = {k for k in before if before[k] == after[k]}
    assert {"living-room", "dining", "kitchen", "bathroom-1"} <= unchanged  # unrelated geometry preserved


def test_4_move_kitchen_beside_living_preserves_unrelated_rooms_and_regenerates(make_session):
    base = sc.fixture_text("small_house")
    s = make_session([sc.REPLY_MOVE_KITCHEN], start_design=base)
    st0 = s.state()
    built0 = st0["status"]["built_at"]
    before = room_rects(st0["model"], "ground-floor")
    r = s.chat(sc.PROMPT_MOVE_KITCHEN)
    assert r.valid
    st = s.state()
    after = room_rects(st["model"], "ground-floor")
    assert after["kitchen"] != before["kitchen"]
    for rid in ("living-room", "dining", "bedroom-1", "bathroom-1"):
        assert after[rid] == before[rid], rid
    # kitchen now shares a wall with the living room: a door joins them
    doors = st["model"]["floors"][0]["doors"]
    assert any({d["room"], d.get("expect_connects")} == {"living-room", "kitchen"} for d in doors)
    # validation re-ran and 2D + 3D + IFC were regenerated
    assert st["status"]["built_at"] > built0 and st["status"]["valid"]
    for rel in [*st["status"]["artifacts"]["svg"], st["status"]["artifacts"]["glb"], st["status"]["artifacts"]["ifc"]]:
        assert os.path.getmtime(os.path.join(outdir(s), rel)) >= built0


def test_5_add_first_floor_with_two_bedrooms(make_session):
    base = sc.fixture_text("small_house")
    s = make_session([sc.REPLY_ADD_FLOOR], start_design=base)
    r = s.chat(sc.PROMPT_ADD_FLOOR)
    assert r.valid, r.status["report"]["errors"]
    st = s.state()
    floors = st["model"]["floors"]
    assert [f["id"] for f in floors] == ["ground-floor", "first-floor"]
    assert sum(1 for x in floors[1]["rooms"] if x["kind"] == "bedroom") == 2
    assert floors[0]["stairs"] and floors[1]["elevation"] == 3.0            # staircase connection
    assert len(st["status"]["artifacts"]["svg"]) == 2                       # one 2D plan per floor
    ifc = ifcopenshell.open(os.path.join(outdir(s), st["status"]["artifacts"]["ifc"]))
    assert len(ifc.by_type("IfcBuildingStorey")) == 2 and len(ifc.by_type("IfcStair")) == 1
    import trimesh
    scene = trimesh.load(os.path.join(outdir(s), st["status"]["artifacts"]["glb"]))
    assert {"floor-ground-floor", "floor-first-floor"} <= set(scene.graph.nodes)


def test_conflicting_or_garbage_llm_output_never_corrupts_design(make_session):
    base = sc.fixture_text("small_house")
    s = make_session(["Sure! Here is the design: ```python\nbuilding = Building(```", "I could not produce valid edits."], start_design=base)
    r = s.chat("Make it a castle")
    assert s.state()["design"] == base and s.state()["status"]["valid"]


def test_prompt_examples_are_themselves_valid(tmp_path):
    """The few-shot examples shown to the LLM must pass the same validator (no teaching invalid habits)."""
    from archagent.agent.prompts import ArchitectPrompts, STARTER_DESIGN
    from archagent.agent.runner import run_workspace
    reply = ArchitectPrompts.example_messages[1]["content"].format(fence=("```", "```"))
    search = reply.split("<<<<<<< SEARCH\n")[1].split("\n=======\n")[0]
    replace = reply.split("\n=======\n")[1].split("\n>>>>>>> REPLACE")[0]
    design = STARTER_DESIGN.replace(search, replace)
    (tmp_path / "design.py").write_text(design)
    ok, text, _ = run_workspace(str(tmp_path))
    assert ok, text
    # and the follow-up example (widen Bedroom 1) stays valid
    reply2 = ArchitectPrompts.example_messages[3]["content"].format(fence=("```", "```"))
    s2 = reply2.split("<<<<<<< SEARCH\n")[1].split("\n=======\n")[0]
    r2 = reply2.split("\n=======\n")[1].split("\n>>>>>>> REPLACE")[0]
    assert s2 in design
    (tmp_path / "design.py").write_text(design.replace(s2, r2))
    ok, text, _ = run_workspace(str(tmp_path))
    assert ok, text
