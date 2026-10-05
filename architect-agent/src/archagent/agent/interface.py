"""The only agent API the rest of the product depends on.

ArchitectureModel, validators and exporters never import Aider. The server talks to this Protocol, so Aider
(agent/session.py + agent/coder.py is the *Aider adapter*) can be swapped for another LLM loop without touching them.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Protocol

# Order in which a turn moves through the pipeline (the frontend shows these).
PHASES = ("idle", "understanding", "generating", "validating", "repairing", "rendering", "ready", "failed")


@dataclass
class ChatResult:
    reply: str
    valid: bool
    rolled_back: bool
    status: Dict[str, Any]
    events: List[Dict[str, Any]] = field(default_factory=list)
    rejected: Optional[Dict[str, Any]] = None

    def to_dict(self):
        return {"reply": self.reply, "valid": self.valid, "rolled_back": self.rolled_back,
                "status": self.status, "events": self.events, "rejected": self.rejected}


class ArchitectureAgent(Protocol):
    workspace: str
    phase: str

    def chat(self, message: str) -> ChatResult: ...
    def state(self) -> Dict[str, Any]: ...
    def rebuild(self) -> Dict[str, Any]: ...
