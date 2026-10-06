"""Safer execution of the LLM-written design.py.

Defence in depth (PoC level - NOT a hardened sandbox, see docs/AUDIT.md):
  1. static check: only `from archagent import ...` / `import math` are allowed; no classes, no dunder access,
     no exec/eval/open/getattr/...; the file is rejected before it runs;
  2. execution in a separate process with a tiny builtins set, empty environment, CPU/memory limits and a wall-clock timeout;
  3. the child returns only the JSON architecture model; the parent never trusts anything else from it.
The long-term fix is to stop executing LLM code and have the LLM emit structured operations instead.
"""
from __future__ import annotations

import ast
import json
import os
import subprocess
import sys
from typing import Any, Dict, List, Optional, Tuple

TIMEOUT_S = 15
ALLOWED_MODULES = {"archagent", "math"}
FORBIDDEN_NAMES = {"exec", "eval", "compile", "open", "__import__", "input", "getattr", "setattr", "delattr", "globals",
                   "locals", "vars", "breakpoint", "memoryview", "exit", "quit", "help", "dir", "type", "super", "object"}
SAFE_BUILTINS = ["range", "len", "min", "max", "sum", "abs", "round", "enumerate", "zip", "list", "dict", "tuple", "set",
                 "float", "int", "str", "bool", "sorted", "reversed", "isinstance", "any", "all", "map", "filter",
                 "ValueError", "TypeError", "KeyError", "Exception", "True", "False", "None"]


def check_source(src: str, filename: str = "design.py") -> List[Dict[str, Any]]:
    """Static policy check. Returns [{'line', 'what'}]; empty list = allowed. SyntaxError is raised to the caller."""
    tree = ast.parse(src, filename)
    problems: List[Dict[str, Any]] = []

    def bad(node, what):
        problems.append({"line": getattr(node, "lineno", 0), "what": what})

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                if a.name.split(".")[0] not in ALLOWED_MODULES:
                    bad(node, f"import of '{a.name}' is not allowed (only archagent and math)")
        elif isinstance(node, ast.ImportFrom):
            if node.level or (node.module or "").split(".")[0] not in ALLOWED_MODULES:
                bad(node, f"import from '{node.module}' is not allowed (only archagent and math)")
        elif isinstance(node, (ast.ClassDef, ast.AsyncFunctionDef, ast.Await, ast.Global, ast.Nonlocal, ast.Try, ast.With)):
            bad(node, f"{type(node).__name__} is not allowed in design.py")
        elif isinstance(node, ast.Attribute) and node.attr.startswith("_"):
            bad(node, f"access to private/dunder attribute '{node.attr}' is not allowed")
        elif isinstance(node, ast.Name) and (node.id in FORBIDDEN_NAMES or (node.id.startswith("__") and node.id != "__name__")):
            bad(node, f"use of '{node.id}' is not allowed")
    return problems


def _scrubbed_env() -> Dict[str, str]:
    here = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))   # .../src
    return {"PYTHONPATH": here, "PATH": "/usr/bin:/bin", "PYTHONIOENCODING": "utf-8", "PYTHONDONTWRITEBYTECODE": "1"}


def run_design_file(path: str, timeout: int = TIMEOUT_S) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
    """Returns (model_dict, error) where error = {code, where, details, hint}."""
    try:
        with open(path, encoding="utf-8") as fh:
            src = fh.read()
    except OSError as e:
        return None, {"code": "DESIGN_MISSING", "where": path, "details": f"Cannot read design file: {e}"}
    try:
        problems = check_source(src, path)
    except SyntaxError as e:
        return None, {"code": "PYTHON_SYNTAX_ERROR", "where": f"{os.path.basename(path)}:{e.lineno}",
                      "details": f"{e.msg} -> {(e.text or '').strip()}",
                      "hint": "Fix the syntax; the file may be truncated or contain stray text from a partial answer."}
    if problems:
        p = problems[0]
        return None, {"code": "DESIGN_FORBIDDEN", "where": f"{os.path.basename(path)}:{p['line']}",
                      "details": "; ".join(f"line {q['line']}: {q['what']}" for q in problems[:5]),
                      "hint": "design.py may only use the archagent SDK (and math). Remove everything else."}
    try:
        proc = subprocess.run([sys.executable, "-s", "-m", "archagent.agent.sandbox", path], capture_output=True, text=True,
                              timeout=timeout, env=_scrubbed_env(), cwd=os.path.dirname(os.path.abspath(path)))
    except subprocess.TimeoutExpired:
        return None, {"code": "DESIGN_TIMEOUT", "where": os.path.basename(path),
                      "details": f"design.py did not finish within {timeout}s (infinite loop or far too much work)."}
    out = proc.stdout.strip().splitlines()
    try:
        payload = json.loads(out[-1])
    except (IndexError, ValueError):
        return None, {"code": "PYTHON_RUNTIME_ERROR", "where": os.path.basename(path),
                      "details": (proc.stderr or "design.py crashed without output").strip()[-400:]}
    if payload.get("ok"):
        return payload["model"], None
    return None, payload["error"]


# ---------------------------------------------------------------------------- child process
def _child(path: str) -> None:     # pragma: no cover  (runs in the subprocess)
    import builtins
    import resource
    import traceback
    resource.setrlimit(resource.RLIMIT_CPU, (TIMEOUT_S, TIMEOUT_S))
    try:
        resource.setrlimit(resource.RLIMIT_AS, (2 * 1024 ** 3, 2 * 1024 ** 3))
    except (ValueError, OSError):
        pass
    src = open(path, encoding="utf-8").read()
    code = compile(src, path, "exec")
    import math
    from archagent import core
    from archagent.core import Building

    real_import = builtins.__import__

    def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name.split(".")[0] not in ALLOWED_MODULES:
            raise ImportError(f"import of '{name}' is not allowed")
        return real_import(name, globals, locals, fromlist, level)

    safe = {n: getattr(builtins, n) for n in SAFE_BUILTINS if hasattr(builtins, n)}
    safe["print"] = lambda *a, **k: None
    safe["__import__"] = guarded_import
    ns: Dict[str, Any] = {"__builtins__": safe, "__name__": "design"}
    try:
        exec(code, ns)
        b = ns.get("building")
        if "building" in ns and b is None:
            err = {"code": "NO_DESIGN_YET", "where": "design.py", "details": "There is no building yet; design.py still contains the placeholder."}
        elif not isinstance(b, Building):
            found = [v for v in ns.values() if isinstance(v, Building)]
            b = found[-1] if found else None
            err = None if b else {"code": "NO_BUILDING", "where": "design.py",
                                  "details": "design.py must create a Building and assign it to a variable named `building`."}
        else:
            err = None
        if err or b is None:
            print(json.dumps({"ok": False, "error": err}))
        else:
            print(json.dumps({"ok": True, "model": b.to_dict()}))
    except BaseException as e:   # noqa: BLE001 - report anything the design did wrong
        tb = traceback.extract_tb(e.__traceback__)
        where = next((f"{os.path.basename(f.filename)}:{f.lineno}" for f in reversed(tb) if f.filename == path), "design.py")
        print(json.dumps({"ok": False, "error": {"code": "PYTHON_RUNTIME_ERROR", "where": where,
                                                  "details": f"{type(e).__name__}: {e}",
                                                  "hint": "Use only the archagent SDK (Building/Floor/add_room/add_door/add_window/add_stair/connect)."}}))


if __name__ == "__main__":     # pragma: no cover
    _child(sys.argv[1])
