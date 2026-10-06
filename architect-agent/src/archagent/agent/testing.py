"""Offline stand-in for the LLM: replays scripted replies through the *real* Aider coder.

Everything except the network call is real: prompt assembly, SEARCH/REPLACE parsing, applying edits, the
validate-and-reflect loop, rollback. Used by the test-suite and for key-less demos.
"""
from __future__ import annotations

from typing import Callable, List, Sequence, Union

Reply = Union[str, Callable[[list], str]]


def install_scripted_llm(coder, replies: Sequence[Reply]):
    queue: List[Reply] = list(replies)
    coder.scripted_calls = []

    def send(messages, model=None, functions=None):
        coder.partial_response_content = ""
        coder.partial_response_function_call = {}
        if not queue:
            coder.partial_response_content = "I have nothing further to change."
            return
        item = queue.pop(0)
        text = item(messages) if callable(item) else item
        coder.scripted_calls.append(messages)
        coder.partial_response_content = text
        coder.io.ai_output(text)
        return
        yield  # pragma: no cover  (makes this a generator like Coder.send)

    coder.send = send
    coder.calculate_and_show_tokens_and_cost = lambda *a, **k: None
    return coder


def edit_reply(thought: str, search: str, replace: str, fence: str = "```") -> str:
    """Builds an Aider SEARCH/REPLACE reply for design.py."""
    return f"{thought}\n\ndesign.py\n{fence}python\n<<<<<<< SEARCH\n{search}\n=======\n{replace}\n>>>>>>> REPLACE\n{fence}\n"


def edit_reply_multi(thought: str, edits, fence: str = "```") -> str:
    """Several SEARCH/REPLACE blocks in one reply: edits = [(search, replace), ...]."""
    blocks = "\n".join(f"design.py\n{fence}python\n<<<<<<< SEARCH\n{a}\n=======\n{b}\n>>>>>>> REPLACE\n{fence}\n" for a, b in edits)
    return f"{thought}\n\n{blocks}"
