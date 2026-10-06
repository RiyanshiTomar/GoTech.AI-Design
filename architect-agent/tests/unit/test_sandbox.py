import os

import pytest

from archagent.agent.runner import run_design
from archagent.agent.sandbox import check_source

HEAD = "from archagent import Building\n"


@pytest.mark.parametrize("src", [
    "import os\n", "import subprocess\n", "from os import system\n", "import socket\n",
    HEAD + "open('/etc/passwd').read()\n", HEAD + "eval('1+1')\n", HEAD + "exec('x=1')\n",
    HEAD + "__import__('os')\n", HEAD + "getattr(Building, '__init__')\n", HEAD + "x = ().__class__.__bases__\n",
    HEAD + "class X: pass\n", HEAD + "try:\n    pass\nexcept Exception:\n    pass\n", HEAD + "with x: pass\n",
])
def test_forbidden_constructs_are_rejected_before_running(src):
    assert check_source(src)


def test_allowed_design_passes_static_check():
    assert check_source(HEAD + "import math\nbuilding = Building(width=math.sqrt(400), depth=30)\n") == []


def test_forbidden_code_never_executes(tmp_path):
    marker = tmp_path / "pwned"
    (tmp_path / "design.py").write_text(f"import os\nopen({str(marker)!r}, 'w').write('x')\n")
    b, err = run_design(str(tmp_path / "design.py"))
    assert b is None and err.code == "DESIGN_FORBIDDEN" and not marker.exists()


def test_infinite_loop_times_out(tmp_path, monkeypatch):
    import archagent.agent.sandbox as sb
    monkeypatch.setattr(sb, "TIMEOUT_S", 2)
    (tmp_path / "design.py").write_text(HEAD + "building = Building(width=10, depth=10)\nwhile True:\n    pass\n")
    model, err = sb.run_design_file(str(tmp_path / "design.py"), timeout=2)
    assert model is None and err["code"] in ("DESIGN_TIMEOUT", "PYTHON_RUNTIME_ERROR")


def test_child_has_no_secrets_in_environment(tmp_path, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-secret")
    from archagent.agent.sandbox import _scrubbed_env
    assert "ANTHROPIC_API_KEY" not in _scrubbed_env()
