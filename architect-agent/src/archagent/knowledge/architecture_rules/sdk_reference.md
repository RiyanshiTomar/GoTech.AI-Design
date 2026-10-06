# SDK reference (everything the agent may write in design.py)

```python
from archagent import Building

building = Building(width=20, depth=30, unit="m", setback=1, name="My House")   # variable MUST be called `building`
building.declare_program(bedroom=3, bathroom=2, kitchen=1, living=1, parking=1)  # the brief; enables feasibility check

ground = building.add_floor("Ground Floor", elevation=0, height=3.0)
ground.add_room("Living Room", x=1, y=1, width=6, depth=5)                       # kind inferred from the name; or kind="bedroom"
ground.add_door("Living Room", "south", offset=2, width=1.2, entrance=True)      # entrance on an exterior wall
ground.connect("Living Room", "Kitchen")                                         # door in the shared wall, auto-placed
ground.add_opening("Living Room", "east", offset=1, width=2.0)                   # open archway
ground.add_window("Living Room", "west", offset=1.5, width=1.5)
ground.add_stair(x=7.2, y=5.2, width=1.0, depth=4.2, direction="north", shape="straight")

first = building.add_floor("First Floor", height=3.0)                            # elevation auto = previous top
```
Room kinds: bedroom, bathroom, kitchen, living, dining, corridor, stair, parking, balcony, terrace, porch, garden, study, utility, pooja, room.
Open kinds (no walls): parking, balcony, terrace, garden, porch.
Do not call validate/export yourself - the system runs them after every edit.
