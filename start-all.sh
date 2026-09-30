#!/usr/bin/env bash
# GoTec.AI - Launch both backend and frontend in separate Git Bash windows

DIR="$(cd "$(dirname "$0")" && pwd)"

echo "[GoTec] Starting backend..."
start "" bash "$DIR/start-backend.sh"

sleep 2

echo "[GoTec] Starting frontend..."
start "" bash "$DIR/start-frontend.sh"

echo ""
echo "Backend:  http://localhost:8000"
echo "Frontend: http://localhost:3000"
echo ""
echo "Both servers starting in separate windows..."
