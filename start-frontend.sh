#!/usr/bin/env bash
# GoTec.AI - Frontend launcher for Git Bash / MINGW64
cd "$(dirname "$0")/frontend/gotec-web" || exit 1

echo "[GoTec] Starting Next.js on http://127.0.0.1:3000"
npm run dev
