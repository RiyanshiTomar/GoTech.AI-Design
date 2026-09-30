#!/usr/bin/env bash
# GoTec.AI - Frontend launcher for Git Bash / MINGW64
set -e
cd "$(dirname "$0")"

echo "[GoTec] Starting Next.js on http://127.0.0.1:3000"
npm run dev
