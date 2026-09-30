"""LLM prompt parser using HuggingFace Inference API"""
import json
import re
from huggingface_hub import InferenceClient
from .config import MODELS, HF_TOKEN
from .schemas import DesignSpec, RoomSpec

SYSTEM_PROMPT = """You are an expert architectural assistant for Indian residential design.
Extract structured information from user prompts and return ONLY valid JSON.

Output format (strict JSON, no markdown, no comments):
{
  "bhk": <int>,
  "total_area_sqft": <float>,
  "facing": "<north|south|east|west>",
  "vastu_compliant": <bool>,
  "rooms": [
    {"type": "<room_name>", "area_sqft": <float>, "attached_bath": <bool>, "vastu_zone": "<direction>"}
  ],
  "floors": <int>,
  "city": "<city_name or null>",
  "notes": "<any extra context>"
}

Room types: master_bedroom, bedroom, kitchen, living_room, dining, pooja_room, bathroom, balcony, store, study
Vastu zones: north, south, east, west, north_east, north_west, south_east, south_west

Example 1:
Input: "3BHK flat, 1200 sqft, north facing, with pooja room, Vastu compliant"
Output: {"bhk":3,"total_area_sqft":1200,"facing":"north","vastu_compliant":true,"rooms":[{"type":"master_bedroom","area_sqft":200,"attached_bath":true,"vastu_zone":"south_west"},{"type":"bedroom","area_sqft":150,"attached_bath":false,"vastu_zone":"south"},{"type":"bedroom","area_sqft":140,"attached_bath":false,"vastu_zone":"west"},{"type":"kitchen","area_sqft":120,"attached_bath":false,"vastu_zone":"south_east"},{"type":"living_room","area_sqft":250,"attached_bath":false,"vastu_zone":"north"},{"type":"dining","area_sqft":100,"attached_bath":false,"vastu_zone":"west"},{"type":"pooja_room","area_sqft":50,"attached_bath":false,"vastu_zone":"north_east"},{"type":"bathroom","area_sqft":40,"attached_bath":false,"vastu_zone":"north_west"},{"type":"bathroom","area_sqft":40,"attached_bath":false,"vastu_zone":"south_west"}],"floors":1,"city":null,"notes":"MIG category"}

Return ONLY the JSON object."""


def parse_prompt_with_llm(prompt: str) -> DesignSpec:
    """Send prompt to HF Inference API and parse to DesignSpec."""
    client = InferenceClient(token=HF_TOKEN) if HF_TOKEN else InferenceClient()

    try:
        response = client.chat_completion(
            model=MODELS["llm"],
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            max_tokens=800,
            temperature=0.2,
        )
        raw = response.choices[0].message.content.strip()
    except Exception as e:
        # Fallback: rule-based parser if LLM unavailable
        return _fallback_parse(prompt, str(e))

    # Extract JSON from response (strip markdown fences if present)
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    raw = raw.strip()

    try:
        data = json.loads(raw)
        rooms = [RoomSpec(**r) for r in data.get("rooms", [])]
        return DesignSpec(
            bhk=data.get("bhk", 2),
            total_area_sqft=float(data.get("total_area_sqft", 1000)),
            facing=data.get("facing", "north"),
            vastu_compliant=bool(data.get("vastu_compliant", True)),
            rooms=rooms,
            floors=int(data.get("floors", 1)),
            city=data.get("city"),
            notes=data.get("notes"),
        )
    except Exception as e:
        return _fallback_parse(prompt, f"Parse error: {e}")


def _fallback_parse(prompt: str, error: str = "") -> DesignSpec:
    """Simple rule-based fallback when LLM fails."""
    p = prompt.lower()
    bhk = 2
    for n in range(1, 6):
        if f"{n}bhk" in p or f"{n} bhk" in p:
            bhk = n
            break

    area = 1000
    m = re.search(r"(\d{3,5})\s*(?:sq|sqft|square)", p)
    if m:
        area = float(m.group(1))

    facing = "north"
    for f in ["north", "south", "east", "west"]:
        if f in p:
            facing = f
            break

    vastu = "vastu" in p
    has_pooja = "pooja" in p

    rooms = [
        RoomSpec(type="master_bedroom", area_sqft=200, attached_bath=True,
                 vastu_zone="south_west" if vastu else None),
        RoomSpec(type="bedroom", area_sqft=150, vastu_zone="south" if vastu else None),
        RoomSpec(type="bedroom" if bhk >= 3 else "kitchen", area_sqft=140 if bhk >= 3 else 120,
                 vastu_zone="west" if vastu else None),
        RoomSpec(type="kitchen", area_sqft=120, vastu_zone="south_east" if vastu else None),
        RoomSpec(type="living_room", area_sqft=250, vastu_zone="north" if vastu else None),
        RoomSpec(type="dining", area_sqft=100),
        RoomSpec(type="bathroom", area_sqft=40),
    ]
    if bhk >= 2:
        rooms.append(RoomSpec(type="bathroom", area_sqft=40))
    if has_pooja:
        rooms.append(RoomSpec(type="pooja_room", area_sqft=50,
                              vastu_zone="north_east" if vastu else None))

    return DesignSpec(
        bhk=bhk,
        total_area_sqft=area,
        facing=facing,
        vastu_compliant=vastu,
        rooms=rooms,
        floors=1,
        notes=f"Fallback parse. LLM error: {error[:100]}",
    )
