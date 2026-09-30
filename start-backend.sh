#!/usr/bin/env bash
# GoTec.AI - Backend launcher for Git Bash / MINGW64
cd "$(dirname "$0")/backend" || exit 1

echo "[GoTec] Activating virtualenv..."
source venv/Scripts/activate

echo "[GoTec] Starting FastAPI on http://127.0.0.1:8000"
uvicorn app.main:app --reload --port 8000
