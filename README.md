# GoTec.AI Design Engine

Write what you want to build. An AI architect designs it, a strict geometry checker validates it, and you get a
2D floor plan, an interactive 3D model and an IFC file. Keep chatting to change the same design.

```
Next.js website (frontend/gotec-web)  <->  Architecture Agent API (architect-agent/)
   /design: chat, 2D plan, 3D model,          Aider-based agent -> design.py -> validation (Shapely)
   model / debug                               -> IFC (IfcOpenShell) + SVG plan + GLB
```

## Run

```bash
# 1. backend (needs one LLM key in architect-agent/.env, see architect-agent/.env.example)
cd architect-agent
pip install -e ../aider && pip install -e ".[test]"
cp .env.example .env
cd .. && ./start-backend.sh        # http://127.0.0.1:8000

# 2. frontend
cd frontend/gotec-web && npm install && npm run dev     # http://localhost:3000/design
```

No key yet? `cd architect-agent && ./scripts/demo.sh` runs a key-less demo on port 8000 (LLM scripted, everything else real)
(the website already points to port 8000). Send: the 20x30 house prompt, then "Make Bedroom 1 one meter wider.", then "Move the kitchen beside the living room."

More details: `architect-agent/README.md` and `architect-agent/docs/ARCHITECTURE.md`.
