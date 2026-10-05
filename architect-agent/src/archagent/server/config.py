"""Runtime configuration from environment variables."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]          # architect-agent/


@dataclass(frozen=True)
class Settings:
    model: str = os.environ.get("ARCH_MODEL", "gpt-4o")
    workspace: Path = Path(os.environ.get("ARCH_WORKSPACE", ROOT / "workspace"))
    host: str = os.environ.get("ARCH_HOST", "127.0.0.1")
    port: int = int(os.environ.get("ARCH_PORT", "8000"))


def get_settings() -> Settings:
    return Settings()
