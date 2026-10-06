# Audit: end-to-end verification

Date: 2026-10-02. Scope: check what is built, fix what is wrong, add no features.
Result: **108 automated tests pass. The three-prompt run works through the existing Next.js `/design` page in a real browser.**
One thing is still scripted: the LLM (see "What was NOT proven").

## 1. Real execution trace

| # | Stage | Where | In -> Out |
|---|---|---|---|
| 1 | Input | `frontend/gotec-web/app/design/page.tsx` | text -> `sendMessage(projectId, text)` |
| 2 | Transport | `lib/api.ts` -> `server/app.py` `POST /api/projects/{id}/messages` | JSON `{message}` -> runs `agent.chat` in a thread |
| 3 | Adapter | `agent/session.py` `ArchitectSession` (implements `agent/interface.py`) | text -> Aider `Coder.run` |
| 4 | Agent loop | `agent/coder.py` `ArchitectureCoder(EditBlockCoder)` | LLM reply -> SEARCH/REPLACE edit of `design.py` |
| 5 | Execute | `agent/sandbox.py` (AST whitelist, subprocess, no env, rlimits, 15 s) | `design.py` -> model dict |
| 6 | Validate | `validation/*` over `geometry/analysis.py` (Shapely) | model -> `{valid, errors[], warnings[]}` |
| 7 | Repair | `coder.run_one` | errors -> next LLM turn; max 6 rounds; else rollback to `last_valid/` |
| 8 | Export (only if valid) | `export/pipeline.py` -> `ifc.py`, `svg.py`, `glb.py` | model -> `.ifc`, `floorplan-*.svg`, `.glb` |
| 9 | Response | `server/app.py` | reply + `state` (status, artifacts, model) |
| 10 | Render | page.tsx (inline SVG) and `components/Viewer3D.tsx` (GLB) | URLs from `status.artifacts`, cache-busted by `built_at` |
| 11 | Follow-up | same project id from `localStorage` -> same `design.py` | small patch, not a rebuild |

The UI reads `GET /api/projects/{id}` every 0.5 s while a message runs, to show the stage.

## 2. Findings and what was done

| Finding | Severity | Status |
|---|---|---|
| IFC geometry was written in mm units while values were metres (20 m would read as 20 mm) | high | **fixed**, unit set to METERS, test checks IFC coordinates |
| `design.py` was run with plain `exec` (a test wrote a file to /tmp) | high | **fixed**, sandbox (`agent/sandbox.py`), tests |
| In a `cm` building, default door/window sizes (0.9, 2.1 ...) were read as cm (9 mm door) | high | **fixed** in `core/floor.py` (defaults are now `"0.9m"` strings), test J |
| Wall ids changed when any wall changed | medium | **fixed**, ids come from axis and span: `g-wall-x0-0-400` |
| Errors had no object ids / severity | medium | **fixed**: `{code, severity, object_ids, objects, message, details}` |
| Aider was called directly by the server | medium | **fixed**: `ArchitectureAgent` protocol, `ArchitectSession` is the only Aider adapter |
| The old frontend client used a single global project (`default`) and the old API | high | **fixed**: project-scoped API; project id stored in the browser; one `POST /api/projects` per browser |
| React dev mode ran the open-project effect twice and made two projects | low | **fixed** (shared promise) |
| Repair limit is 6, not 5 | info | documented |
| Docs listed validator codes that did not exist | low | **fixed**, test now compares docs and code |

## 3. Responsibilities

* LLM: reasoning and writing the edit. It never decides validity and never sees the renderers.
* Model (`Building.to_dict()`): one truth. Every exporter reads the same `Analysis`.
* Validator: the only authority on geometry. Hard rules fail (`ERROR`), heuristics only warn (`WARNING`).
* Exporters: never decide. If validation fails nothing new is drawn; old files are kept and marked `stale`.
* Browser: draws what the server sends. It does not compute geometry.

Checked in the run: for all 9 rooms, SVG width/height / 50 = model width/depth; the SVG keeps its aspect (viewBox 1140 x 1670).
The Y-up conversion for 3D happens in one place (`export/glb.py`, `_Mesh.box`).

## 4. One dimension convention

Metres are canonical inside the model. `Building(unit=...)` converts inputs (`m, cm, mm, ft, in`) once, at the SDK door;
strings with units work too (`"65.6ft"`). Rooms are axis-aligned rectangles: `x, y` = south-west corner, `width` along x, `depth` along y.
Exterior walls sit inside the room box; interior walls are centred on the shared edge. Touching edges are valid, overlap is not.

## 5. Scenarios A-J (automated, `tests/integration/test_audit.py`)

A room wider than building -> `ROOM_OUTSIDE_SITE`. B 100 bedrooms in 20x20 -> `PROGRAM_INFEASIBLE`, nothing rendered.
C width -4 -> `NEGATIVE_DIMENSION`. D bathroom moved 100 m east -> `ROOM_OUTSIDE_SITE`. E door removal -> unreachable rooms.
F 5 m door in 3 m wall -> door error. G add floor -> stair + landing + support rules. H move Bedroom 1 by 20 cm -> only that room changes.
I smaller site -> bounds errors, previous design kept. J all dimensions in cm -> identical model to metres.

## 6. Existing-frontend run (real browser, Playwright, Chromium)

Script: `e2e_ui.py` style run; screenshots in `e2e/`.

1. Open `/design` -> one `POST /api/projects`, id stored.
2. Prompt 1 -> 9 rooms, plan + 3D + IFC.
3. Prompt 2 in the same project (same id on all 3 message requests). Naive edit overlapped Bedroom 2; validator caught it; repair moved Bedroom 2.
   Changed rooms: only `bedroom-1` (5 -> 6 m wide) and `bedroom-2` (x 6 -> 7, width 6 -> 5). Everything else identical.
4. Prompt 3 -> only `kitchen` and `dining` changed (swapped). Plan and 3D refreshed with no page reload.
5. Reload page -> same project id, plan restored.
No console errors. GLB loaded in the Three.js viewer (orbit / zoom / pan / reset).

## 7. What was NOT proven (be careful)

* **The LLM was scripted.** Aider, prompts, parsing, validator, repair, exporters, API and UI are real. The model's own replies were written by me.
  A real model may write worse edits; the repair loop and rollback are the protection. Run with a real key before trusting quality.
* The UI chip showed "Generating..." and "Building plan..." but the fast scripted run was too quick for the poller to catch "Repairing"; that phase is covered by backend tests.
* `PLANNING` is not a separate server phase yet (UI maps what the server reports).
* The sandbox is PoC level, not a security boundary. Do not expose the server to untrusted users.
* Failure display (rollback message in the chat) is covered by backend tests, not by this browser run.
* Walls are derived, so a wall id changes if its centre line moves.

## 8. Recommendation

Replace "LLM writes Python" with "LLM emits structured operations", e.g.
`{"action":"update_room","room_id":"bedroom-1","changes":{"width":6}}`, applied by a small deterministic engine to a cloned model,
then validated, then committed or dropped. It removes code execution, makes edits diffable, and makes every change auditable.
The `ArchitectureAgent` interface is already the seam where that swap happens.
