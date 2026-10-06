"""Knowledge layer: markdown rule files the agent reads, plus the loader that builds its brief."""
from __future__ import annotations

from pathlib import Path
from typing import Dict

RULES_DIR = Path(__file__).parent / "architecture_rules"


def load_rules() -> Dict[str, str]:
    return {p.stem: p.read_text(encoding="utf-8") for p in sorted(RULES_DIR.glob("*.md"))}


def rules_brief() -> str:
    """All rule files concatenated, in filename order, for inclusion in the system prompt."""
    return "\n\n".join(f"<!-- {name} -->\n{text}" for name, text in load_rules().items())
