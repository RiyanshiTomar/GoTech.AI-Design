"""Projects: one project = one workspace folder = one persistent ArchitectureModel + one agent conversation."""
from __future__ import annotations

import re
import secrets
import threading
from pathlib import Path
from typing import Callable, Dict, List, Optional

from ..agent.interface import ArchitectureAgent

_ID = re.compile(r"^p_[0-9a-f]{8}$")


class ProjectStore:
    def __init__(self, root: Path, factory: Callable[[str], ArchitectureAgent]):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self._factory = factory
        self._agents: Dict[str, ArchitectureAgent] = {}
        self._lock = threading.Lock()

    @staticmethod
    def valid_id(pid: str) -> bool:
        return bool(_ID.match(pid or ""))

    def path(self, pid: str) -> Path:
        return self.root / pid

    def create(self) -> str:
        with self._lock:
            while True:
                pid = "p_" + secrets.token_hex(4)
                if not self.path(pid).exists():
                    break
            self._agents[pid] = self._factory(str(self.path(pid)))
            return pid

    def exists(self, pid: str) -> bool:
        return self.valid_id(pid) and (pid in self._agents or self.path(pid).is_dir())

    def get(self, pid: str) -> Optional[ArchitectureAgent]:
        """Existing project only (never creates one implicitly)."""
        if not self.exists(pid):
            return None
        with self._lock:
            if pid not in self._agents:
                self._agents[pid] = self._factory(str(self.path(pid)))   # re-attach after a server restart; model is on disk
            return self._agents[pid]

    def list(self) -> List[str]:
        return sorted(p.name for p in self.root.iterdir() if p.is_dir() and self.valid_id(p.name))
