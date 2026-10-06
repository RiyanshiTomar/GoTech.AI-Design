"""Key-less demo: the real server + real Aider loop, with a scripted stand-in for the LLM.

    PYTHONPATH=src:. python scripts/demo_server.py
Send, in order: the 20x30 house, 'Make Bedroom 1 one meter wider.', 'Move the kitchen beside the living room.'
Only the LLM is scripted; Aider, validator, exporters, API and UI are real.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import uvicorn  # noqa: E402

from archagent.agent.session import ArchitectSession  # noqa: E402
from archagent.agent.testing import install_scripted_llm  # noqa: E402
from archagent.server import create_app  # noqa: E402
from archagent.server.config import get_settings  # noqa: E402
from tests.support import scenarios as sc  # noqa: E402


def factory(ws):
    s = ArchitectSession(ws, model="gpt-4o")
    install_scripted_llm(s.coder, [sc.REPLY_E2E_CREATE, sc.REPLY_E2E_WIDEN_NAIVE, sc.REPLY_E2E_WIDEN_REPAIR, sc.REPLY_E2E_MOVE_KITCHEN])
    return s


if __name__ == "__main__":
    st = get_settings()
    uvicorn.run(create_app(st, session_factory=factory), host=st.host, port=st.port)
