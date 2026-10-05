import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

import pytest  # noqa: E402

from archagent.agent.session import ArchitectSession  # noqa: E402
from archagent.agent.testing import install_scripted_llm  # noqa: E402


@pytest.fixture
def make_session(tmp_path):
    """ArchitectSession on a temp workspace whose LLM replies are scripted (everything else is real)."""
    def _make(replies, start_design=None):
        ws = tmp_path / "ws"
        s = ArchitectSession(str(ws), model="gpt-4o")
        if start_design is not None:
            (ws / "design.py").write_text(start_design, encoding="utf-8")
            s.rebuild()
        install_scripted_llm(s.coder, replies)
        return s
    return _make


def codes(report_dict, key="errors"):
    return {e["code"] for e in report_dict[key]}


def room_rects(model, floor_id):
    f = next(f for f in model["floors"] if f["id"] == floor_id)
    return {r["id"]: (r["x"], r["y"], r["width"], r["depth"]) for r in f["rooms"]}
