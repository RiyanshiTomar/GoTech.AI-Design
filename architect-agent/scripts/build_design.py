"""Run a design.py through validate -> SVG/IFC/GLB without any LLM:  python scripts/build_design.py path/to/workspace"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from archagent.agent.runner import main  # noqa: E402

sys.exit(main())
