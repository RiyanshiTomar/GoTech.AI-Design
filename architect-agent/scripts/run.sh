#!/usr/bin/env bash
# Start the Architecture Agent UI (needs an LLM key in .env, see .env.example)
set -e
cd "$(dirname "$0")/.."
export PYTHONPATH="$PWD/src:$PYTHONPATH"
exec python -m archagent.server
