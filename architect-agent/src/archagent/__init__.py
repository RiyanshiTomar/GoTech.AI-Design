"""archagent -- AI Architecture Agent (PoC), built on Aider.

Layers (each a sub-package):
    core        domain model + the small SDK the LLM writes code against
    geometry    deterministic derivation of walls / openings / slabs / stairs
    validation  the geometric authority (Shapely based, structured errors)
    export      IFC (IfcOpenShell), 2D SVG, 3D GLB
    agent       Aider integration: prompts, coder, build runner, session
    knowledge   architecture rules the agent reads (hard rules vs heuristics)
    server      FastAPI project API used by the existing Next.js frontend (frontend/gotec-web)
"""
from .core import Building, Floor, Room, Door, Window, Stair  # noqa: F401

__version__ = "0.1.0"
