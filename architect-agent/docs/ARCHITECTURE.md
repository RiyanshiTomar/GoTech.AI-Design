# Architecture notes

## What was reused from Aider (inspected in `aider/coders/base_coder.py`)

| Need | Aider piece | How we use it |
|---|---|---|
| conversational loop + state | `Coder.run_one`, `cur_messages`/`done_messages` | unchanged; one coder per project keeps the chat |
| code generation + file editing | `EditBlockCoder` (SEARCH/REPLACE) | subclassed as `ArchitectureCoder`; edits **only** `design.py`, so follow-ups are small patches that preserve unrelated geometry |
| prompts | `CoderPrompts` classes (`main_system`, `example_messages`, `system_reminder`) | `agent/prompts.py::ArchitectPrompts` = architecture persona + all `knowledge/*.md` |
| execution + observation + retry | `auto_test` / `test_cmd` (callable returns error text) and `reflected_message`, `max_reflections` | `test_cmd` = `runner.run_workspace` (exec design.py -> validate -> render); its failure text is the next user turn for the LLM; `max_reflections = 6` |
| model access, retries | litellm via `Model`, `send_message` | unchanged (any provider key) |

Bypassed / switched off: git repo handling, repo map, lint, URL scraping, shell-command suggestions, voice, browser GUI, analytics.
Coupling worth knowing: `Coder.get_platform_info` concatenates `test_cmd` as a string, so the coder overrides it (our `test_cmd` is a callable).

## Single source of truth

`workspace/<project>/design.py` is the editable source (PoC). The product's single source of truth is the model JSON it produces; see `docs/AUDIT.md` (Python DSL). Running it yields the JSON model
(`out/model.json`, schema v1). Everything downstream (validators, IFC, SVG, GLB) consumes the **same** `geometry.analysis.Analysis`,
so validators and renderers cannot disagree about where walls, openings, slabs or stairs are.

## Safety properties

* Renderers run only if validation passes; failed exports mark the previous artifacts `stale`.
* After every user turn the coder re-validates `design.py`; if it is invalid the previous valid version is restored (`rolled_back`).
* Impossible briefs surface as `PROGRAM_INFEASIBLE` (needs `building.declare_program(...)`), and the agent is instructed to explain with numbers.
* Validator crashes fail closed (`VALIDATOR_ERROR`).

## Known PoC limits

Rectangular axis-aligned rooms, one rectangle per room, <=4 floors, straight/U stairs only, no roof (SDK mentions none yet),
no irregular plots. Real LLM behaviour has only been exercised through a scripted stand-in in this repo's tests; prompt quality
should be tuned with a real model.
