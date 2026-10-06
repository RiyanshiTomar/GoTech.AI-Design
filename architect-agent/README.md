# Architecture Agent (PoC)

Natural language -> valid building. Built on [Aider](../aider): its chat loop, edit-block parsing and
"run a command, feed the failure back, retry" loop are reused; the product on top is architecture, not software.

```
USER PROMPT
  -> Aider-based architecture agent (reasons like an architect)
  -> edits design.py  (Python written against a tiny SDK: Building / Floor / add_room / add_door / add_window / add_stair)
  -> deterministic validation (Shapely)      <- the geometric authority; the LLM never decides validity
       invalid -> structured errors go back to the agent -> it repairs -> validate again (up to 6 rounds, else rollback)
       valid   -> IFC (IfcOpenShell) + 2D SVG per floor + 3D GLB
  -> the GoTec Next.js app (/design): 2D PLAN | 3D MODEL (Three.js) | MODEL / DEBUG, plus chat to keep editing the same project
```

## Run it

```bash
cd architect-agent
pip install -e ../aider            # the Aider clone next to this folder (or: pip install aider-chat)
pip install -e ".[test]"
cp .env.example .env               # add ONE LLM key + ARCH_MODEL
./scripts/run.sh                   # API on http://127.0.0.1:8000  (UI = the Next.js app in frontend/gotec-web)
```

No key yet? `./scripts/demo.sh` runs the same server and the same Aider loop with a scripted stand-in for the LLM
(send, in order: the 20x30 house, "Make Bedroom 1 one meter wider.", "Move the kitchen beside the living room.").

Tests (no network, no key): `python -m pytest`

## Folder structure

```
architect-agent/
  src/archagent/
    core/         domain model + the SDK the LLM writes against (Building, Floor, Room, Door, Window, Stair, units)
    geometry/     deterministic derivation: walls, openings, stairs, slabs  (shared by validators AND exporters)
    validation/   one module per rule family; structured errors {code, objects, details, hint}; warnings = heuristics
    export/       ifc.py (IfcOpenShell) | svg.py (2D plan) | glb.py (3D) | pipeline.py (validate, then render)
    agent/        interface.py (ArchitectureAgent contract) | sandbox.py (runs design.py in a locked subprocess) | prompts.py | coder.py (Aider Coder subclass) | runner.py (design.py -> validate -> artifacts)
                  session.py (one project = one workspace + chat state) | io.py | testing.py (scripted LLM)
    knowledge/    architecture_rules/*.md  (HARD RULES vs HEURISTICS) + loader that feeds the system prompt
    server/       FastAPI, project-scoped: POST /api/projects, GET /api/projects/{id}, POST .../messages, GET .../files/*
  tests/          unit/ (corner cases, exporters, runner) | integration/ (5 scenarios, server) | fixtures/ | support/
  workspace/      one folder per project: design.py (source of truth), out/{model.json,status.json,artifacts/}
  docs/ARCHITECTURE.md   how Aider was reused, design decisions
```

## Rules the system enforces (see `knowledge/architecture_rules/`)

Hard rules (fail validation, nothing is rendered): rooms inside plot and setback, no overlaps, valid dimensions/units,
walls valid, doors/windows on real walls and fitting, windows on exterior walls, stairs inside one room with enough run
and an exit landing above, upper rooms supported by the floor below, every room reachable from the entrance, every floor
connected by a stair, duplicate ids, programme feasibility. Heuristics (warnings only): daylight, proportions,
kitchen adjacency, bathroom access.

The numeric limits are PoC practical defaults, **not** building-code citations.
