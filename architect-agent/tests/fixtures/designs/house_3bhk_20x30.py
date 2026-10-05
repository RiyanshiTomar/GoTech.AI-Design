"""Reference answer for: 'Create a 20m x 30m single-floor 3BHK with kitchen, living room, two bathrooms and parking.'"""
from archagent import Building

building = Building(width=20, depth=30, unit="m", setback=1, name="3BHK House")
building.declare_program(bedroom=3, bathroom=2, kitchen=1, living=1, parking=1)

g = building.add_floor("Ground Floor", elevation=0, height=3.0)

g.add_room("Living Room", 1, 1, 8, 6)
g.add_room("Kitchen", 9, 1, 5, 6)
g.add_room("Bathroom 2", 14, 1, 5, 3)
g.add_room("Dining", 14, 4, 5, 3)
g.add_room("Corridor", 1, 7, 18, 2, kind="corridor")
g.add_room("Master Bedroom", 1, 9, 7, 7)
g.add_room("Bedroom 2", 8, 9, 6, 7)
g.add_room("Bedroom 3", 14, 9, 5, 7)
g.add_room("Bathroom 1", 1, 16, 4, 3)
g.add_room("Parking", 10, 19, 8, 9, kind="parking")

g.add_door("Living Room", "south", 3, width=1.2, entrance=True)
g.connect("Living Room", "Kitchen")
g.connect("Kitchen", "Dining")
g.connect("Dining", "Bathroom 2")
g.connect("Living Room", "Corridor")
g.connect("Dining", "Corridor")
g.connect("Corridor", "Master Bedroom")
g.connect("Corridor", "Bedroom 2")
g.connect("Corridor", "Bedroom 3")
g.connect("Master Bedroom", "Bathroom 1")

for room, side, off in [("Living Room", "south", 6.2), ("Living Room", "west", 2), ("Kitchen", "south", 1.5),
                        ("Bathroom 2", "east", 0.8), ("Dining", "east", 0.8), ("Master Bedroom", "west", 2.5),
                        ("Bedroom 2", "north", 2), ("Bedroom 3", "east", 2.5), ("Bedroom 3", "north", 1.5),
                        ("Bathroom 1", "west", 1)]:
    g.add_window(room, side, off, width=1.2 if room not in ("Bathroom 1", "Bathroom 2") else 0.6)
