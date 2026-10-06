"""Names, ids and room-kind inference."""
from __future__ import annotations

import re

_KIND_KEYWORDS = [
    ("master", "bedroom"), ("bedroom", "bedroom"), ("bed room", "bedroom"), ("guest room", "bedroom"),
    ("bath", "bathroom"), ("toilet", "bathroom"), ("wc", "bathroom"), ("washroom", "bathroom"),
    ("kitchen", "kitchen"), ("dining", "dining"), ("living", "living"), ("lounge", "living"),
    ("hall", "living"), ("corridor", "corridor"), ("passage", "corridor"), ("lobby", "corridor"),
    ("stair", "stair"), ("parking", "parking"), ("garage", "parking"), ("carport", "parking"),
    ("balcony", "balcony"), ("terrace", "terrace"), ("porch", "porch"), ("garden", "garden"),
    ("pooja", "pooja"), ("puja", "pooja"), ("study", "study"), ("office", "study"),
    ("store", "utility"), ("utility", "utility"), ("laundry", "utility"),
]


def infer_kind(name: str) -> str:
    low = name.lower()
    for key, kind in _KIND_KEYWORDS:
        if key in low:
            return kind
    return "room"


def slugify(text) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", str(text).lower()).strip("-")
    return s or "item"
