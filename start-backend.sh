#!/usr/bin/env bash
# GoTec.AI - starts the Architecture Agent backend on http://127.0.0.1:8000
cd "$(dirname "$0")/architect-agent" || exit 1
[ -f .venv/bin/activate ] && source .venv/bin/activate
export PYTHONPATH="$PWD/src:$PYTHONPATH"
export ARCH_PORT="${ARCH_PORT:-8000}"
echo "[GoTec] Architecture Agent on http://127.0.0.1:$ARCH_PORT"
exec python3 -m archagent.server
