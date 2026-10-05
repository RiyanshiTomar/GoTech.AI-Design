"""HTTP API of the architecture engine (consumed by the existing Next.js frontend).

POST /api/projects                      create a project            -> {project_id}
GET  /api/projects                      list project ids
GET  /api/projects/{id}                 current state (+ phase)     -> {phase, design, model, status}
POST /api/projects/{id}/messages        chat turn on THAT project   -> {reply, valid, rolled_back, rejected, state}
POST /api/projects/{id}/rebuild         re-run validation + exports from the stored model (no LLM)
GET  /api/projects/{id}/model           the ArchitectureModel (model.json)
GET  /api/projects/{id}/floorplan?floor=<floor_id>   2D plan SVG
GET  /api/projects/{id}/model3d         GLB
GET  /api/projects/{id}/ifc             IFC
GET  /api/projects/{id}/files/{path}    any generated artifact
Nothing here makes architectural decisions: it forwards to the agent and serves files.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Callable, Optional

from fastapi import FastAPI, HTTPException
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field

from ..agent.interface import ArchitectureAgent
from ..agent.session import ArchitectSession
from .config import Settings, get_settings
from .projects import ProjectStore

MEDIA = {".svg": "image/svg+xml", ".glb": "model/gltf-binary", ".ifc": "application/x-step", ".json": "application/json"}


class MessageIn(BaseModel):
    message: str = Field(min_length=1, max_length=4000)


def create_app(settings: Optional[Settings] = None,
               session_factory: Optional[Callable[[str], ArchitectureAgent]] = None) -> FastAPI:
    st = settings or get_settings()
    factory = session_factory or (lambda ws: ArchitectSession(ws, model=st.model))
    store = ProjectStore(st.workspace, factory)
    app = FastAPI(title="Architecture Engine", version="0.2.0")
    origins = [o for o in os.environ.get("FRONTEND_URL", "http://localhost:3000").split(",") if o]
    app.add_middleware(CORSMiddleware, allow_origins=origins + ["http://127.0.0.1:3000"], allow_methods=["*"], allow_headers=["*"])

    def agent(pid: str) -> ArchitectureAgent:
        a = store.get(pid)
        if a is None:
            raise HTTPException(404, "project not found")
        return a

    def full_state(pid: str, a: ArchitectureAgent) -> dict:
        return {"project_id": pid, "phase": a.phase, **a.state()}

    def out_file(pid: str, rel: str) -> FileResponse:
        agent(pid)
        base = (store.path(pid) / "out").resolve()
        target = (base / rel).resolve()
        if base not in target.parents or not target.is_file():
            raise HTTPException(404, "not found")
        return FileResponse(target, media_type=MEDIA.get(target.suffix, "application/octet-stream"),
                            headers={"Cache-Control": "no-store"})

    @app.get("/api/health")
    def health():
        return {"ok": True, "model": st.model}

    @app.post("/api/projects")
    def create_project():
        pid = store.create()
        return full_state(pid, agent(pid))

    @app.get("/api/projects")
    def list_projects():
        return {"projects": store.list()}

    @app.get("/api/projects/{pid}")
    def get_project(pid: str):
        return full_state(pid, agent(pid))

    @app.post("/api/projects/{pid}/messages")
    async def post_message(pid: str, body: MessageIn):
        a = agent(pid)
        try:
            result = await run_in_threadpool(a.chat, body.message)
        except Exception as e:      # LLM / key / network failures reach the UI as JSON; the last valid design stays untouched
            return JSONResponse({"error": f"{type(e).__name__}: {e}", "state": full_state(pid, a)}, status_code=502)
        return {**result.to_dict(), "state": full_state(pid, a)}

    @app.post("/api/projects/{pid}/rebuild")
    async def rebuild(pid: str):
        a = agent(pid)
        await run_in_threadpool(a.rebuild)
        return full_state(pid, a)

    @app.get("/api/projects/{pid}/model")
    def model(pid: str):
        return out_file(pid, "model.json")

    @app.get("/api/projects/{pid}/floorplan")
    def floorplan(pid: str, floor: Optional[str] = None):
        svgs = (agent(pid).state()["status"].get("artifacts") or {}).get("svg") or []
        if not svgs:
            raise HTTPException(404, "no valid plan yet")
        if floor:
            match = [p for p in svgs if p.endswith(f"floorplan-{floor}.svg")]
            if not match:
                raise HTTPException(404, "unknown floor")
            return out_file(pid, match[0])
        return out_file(pid, svgs[0])

    @app.get("/api/projects/{pid}/model3d")
    def model3d(pid: str):
        glb = (agent(pid).state()["status"].get("artifacts") or {}).get("glb")
        if not glb:
            raise HTTPException(404, "no valid 3D model yet")
        return out_file(pid, glb)

    @app.get("/api/projects/{pid}/ifc")
    def ifc(pid: str):
        f = (agent(pid).state()["status"].get("artifacts") or {}).get("ifc")
        if not f:
            raise HTTPException(404, "no valid IFC yet")
        return out_file(pid, f)

    @app.get("/api/projects/{pid}/files/{path:path}")
    def files(pid: str, path: str):
        return out_file(pid, path)

    return app
