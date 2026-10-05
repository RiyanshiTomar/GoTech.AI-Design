#!/usr/bin/env bash
# Key-less demo: real server + real Aider loop, scripted stand-in for the LLM (first prompt builds the 3BHK).
set -e
cd "$(dirname "$0")/.."
export PYTHONPATH="$PWD/src:$PWD:$PYTHONPATH"
exec python scripts/demo_server.py
