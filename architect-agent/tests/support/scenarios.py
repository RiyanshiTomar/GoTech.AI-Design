"""Scripted 'LLM' replies for the five required scenarios. Real Aider loop, fake network."""
from __future__ import annotations

from pathlib import Path

from archagent.agent.testing import edit_reply, edit_reply_multi

FIX = Path(__file__).resolve().parents[1] / "fixtures" / "designs"


def fixture_text(name: str) -> str:
    return (FIX / f"{name}.py").read_text(encoding="utf-8")


def fixture_body(name: str) -> str:
    """Fixture without its docstring and import line (what goes after the starter's `from archagent import Building`)."""
    lines = fixture_text(name).splitlines()
    out, skip_doc = [], False
    for ln in lines:
        if ln.startswith('"""') and not skip_doc:
            if ln.count('"""') >= 2:
                continue
            skip_doc = True
            continue
        if skip_doc:
            if '"""' in ln:
                skip_doc = False
            continue
        if ln.startswith("from archagent import"):
            continue
        out.append(ln)
    return "\n".join(out).strip("\n")


def create_reply(name: str, thought: str) -> str:
    return edit_reply(thought, "building = None", fixture_body(name))


# 1 ------------------------------------------------------------------------------------------------
PROMPT_3BHK = "Create a 20m × 30m single-floor 3BHK with kitchen, living room, two bathrooms and parking."
REPLY_3BHK = create_reply(
    "house_3bhk_20x30",
    "Plot 20 x 30 m with a 1 m setback gives a 18 x 28 m region. Programme: 3 bedrooms, 2 bathrooms, kitchen, living, parking. "
    "Public zone south (living, kitchen, dining, bathroom) off the entrance, a 2 m corridor, three bedrooms north of it, "
    "an attached bathroom to the master, parking in the north-east.")

# 2 ------------------------------------------------------------------------------------------------
PROMPT_30_BEDROOMS = "Create a 10m × 10m house with 30 bedrooms."
REPLY_30_BEDROOMS_ATTEMPT = edit_reply(
    "I will declare the brief so the validator can check feasibility, with one bedroom placed inside the plot.",
    "building = None",
    'building = Building(width=10, depth=10, unit="m", setback=0.5)\n'
    'building.declare_program(bedroom=30)\n'
    'g = building.add_floor("Ground Floor", height=3.0)\n'
    'g.add_room("Bedroom 1", 0.5, 0.5, 5, 5)\n'
    'g.add_door("Bedroom 1", "south", 1, entrance=True)\n'
    'g.add_window("Bedroom 1", "west", 1.5)')
REPLY_30_BEDROOMS_EXPLAIN = (
    "30 bedrooms cannot reasonably fit: at the 9 m2 minimum they need 270 m2, while a 10 x 10 m plot with a 0.5 m setback "
    "offers about 130 m2 over two floors. I have not changed the design. Options: fewer bedrooms (about 8 fit on two floors), "
    "a plot of roughly 20 x 20 m with 4 floors, or very small hostel-style rooms if you can accept sub-minimum sizes.")

# 3 ------------------------------------------------------------------------------------------------
PROMPT_WIDEN_5 = "Increase Bedroom 1 width by 5m."
REPLY_WIDEN_5_NAIVE = edit_reply(
    "Bedroom 1 is 3 m wide; adding 5 m makes it 8 m.",
    'ground.add_room("Bedroom 1", 0.5, 5.5, 3, 3)', 'ground.add_room("Bedroom 1", 0.5, 5.5, 8, 3)')
REPLY_WIDEN_5_EXPLAIN = (
    "Bedroom 1 cannot be 8 m wide here: the row it sits in is only 11 m wide and also holds the study and kitchen, so an 8 m bedroom "
    "overlaps them and leaves no room for the rest. I restored the previous layout. I can widen it by up to about 1 m, "
    "or rebuild the row with a smaller study if you want a larger bedroom.")

PROMPT_WIDEN_1 = "Increase Bedroom 1 width by 1m."
REPLY_WIDEN_1_NAIVE = edit_reply(
    "Bedroom 1 goes from 3 m to 4 m wide.",
    'ground.add_room("Bedroom 1", 0.5, 5.5, 3, 3)', 'ground.add_room("Bedroom 1", 0.5, 5.5, 4, 3)')
REPLY_WIDEN_1_REPAIR = edit_reply(
    "The wider bedroom overlaps the Study. I shift the Study 1 m east and make it 3 m wide; the Kitchen and everything else stay.",
    'ground.add_room("Study", 3.5, 5.5, 4, 3)', 'ground.add_room("Study", 4.5, 5.5, 3, 3)')

# 4 ------------------------------------------------------------------------------------------------
PROMPT_MOVE_KITCHEN = "Move the kitchen beside the living room."
REPLY_MOVE_KITCHEN = edit_reply_multi(
    "The Study already sits against the Living Room, so I swap the Study and the Kitchen; both are 4 x 3 m. No other room moves. "
    "The doors and windows that belonged to them are re-attached.",
    [('ground.add_room("Study", 3.5, 5.5, 4, 3)\nground.add_room("Kitchen", 7.5, 5.5, 4, 3)',
      'ground.add_room("Kitchen", 3.5, 5.5, 4, 3)\nground.add_room("Study", 7.5, 5.5, 4, 3)'),
     ('ground.connect("Living Room", "Study")', 'ground.connect("Living Room", "Kitchen")'),
     ('ground.connect("Dining", "Kitchen")', 'ground.connect("Dining", "Study")'),
     ('ground.add_window("Study", "north", 1.4, width=1.2)', 'ground.add_window("Kitchen", "north", 1.4, width=1.2)'),
     ('ground.add_window("Kitchen", "east", 0.9, width=1.2)', 'ground.add_window("Study", "east", 0.9, width=1.2)')])

# 5 ------------------------------------------------------------------------------------------------
PROMPT_ADD_FLOOR = "Add a first floor with two bedrooms."
_ADD = (FIX / "first_floor_addition.py").read_text(encoding="utf-8").split("\n", 1)[1].strip("\n")
REPLY_ADD_FLOOR = edit_reply(
    "The stair goes in the Living Room (it is the only ground room large enough), running east with its exit landing on a new "
    "first-floor Landing above it. Bedrooms 2 and 3 open off the Landing and sit over existing ground rooms.",
    'ground.add_window("Bathroom 1", "west", 0.7, width=0.6)',
    'ground.add_window("Bathroom 1", "west", 0.7, width=0.6)\n\n' + _ADD)

# 6 -- the three-prompt end-to-end run (used by scripts/demo_server.py and the Playwright check) ---------
PROMPT_E2E_1 = "Create a 20m × 30m house with 3 bedrooms, a living room, kitchen and 2 bathrooms."
REPLY_E2E_CREATE = create_reply(
    "house_20x30_e2e",
    "Plot 20 x 30 m with a 1 m setback gives an 18 x 28 m region. Public rooms in a south row (living, dining, kitchen), "
    "a 2 m corridor, three bedrooms north of it, and one bathroom attached to Bedroom 1 and one to Bedroom 3.")

PROMPT_E2E_2 = "Make Bedroom 1 one meter wider."
REPLY_E2E_WIDEN_NAIVE = edit_reply(
    "Bedroom 1 goes from 5 m to 6 m wide.",
    'ground.add_room("Bedroom 1", 1, 9, 5, 8)', 'ground.add_room("Bedroom 1", 1, 9, 6, 8)')
REPLY_E2E_WIDEN_REPAIR = edit_reply(
    "The wider Bedroom 1 now overlaps Bedroom 2. I move Bedroom 2 one metre east and make it one metre narrower; "
    "Bedroom 3 and every other room stay as they are.",
    'ground.add_room("Bedroom 2", 6, 9, 6, 8)', 'ground.add_room("Bedroom 2", 7, 9, 5, 8)')

PROMPT_E2E_3 = "Move the kitchen beside the living room."
REPLY_E2E_MOVE_KITCHEN = edit_reply_multi(
    "The Dining room sits between the Living Room and the Kitchen. I swap Dining and Kitchen. Only these two rooms, their doors "
    "and their windows change.",
    [('ground.add_room("Dining", 8, 1, 5, 6)\nground.add_room("Kitchen", 13, 1, 6, 6)',
      'ground.add_room("Kitchen", 8, 1, 6, 6)\nground.add_room("Dining", 14, 1, 5, 6)'),
     ('ground.connect("Living Room", "Dining")', 'ground.connect("Living Room", "Kitchen")'),
     ('ground.connect("Dining", "Kitchen")', 'ground.connect("Kitchen", "Dining")'),
     ('ground.add_window("Dining", "south", 1.8)\nground.add_window("Kitchen", "south", 2.4)\nground.add_window("Kitchen", "east", 2.4)',
      'ground.add_window("Kitchen", "south", 1.8)\nground.add_window("Dining", "south", 1.8)\nground.add_window("Dining", "east", 2.4)')])
