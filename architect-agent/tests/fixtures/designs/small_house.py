"""Base design used by the modification tests: 12 x 14 m plot, one floor, packed rooms."""
from archagent import Building

building = Building(width=12, depth=14, unit="m", setback=0.5, name="Small House")
building.declare_program(living=1, dining=1, kitchen=1, bedroom=1, bathroom=1, study=1)

ground = building.add_floor("Ground Floor", elevation=0, height=3.0)
ground.add_room("Living Room", 0.5, 0.5, 6, 5)
ground.add_room("Dining", 6.5, 0.5, 5, 5)
ground.add_room("Bedroom 1", 0.5, 5.5, 3, 3)
ground.add_room("Study", 3.5, 5.5, 4, 3)
ground.add_room("Kitchen", 7.5, 5.5, 4, 3)
ground.add_room("Bathroom 1", 0.5, 8.5, 3, 2.5)

ground.add_door("Living Room", "south", 2.0, width=1.0, entrance=True)
ground.connect("Living Room", "Dining")
ground.connect("Living Room", "Study")
ground.connect("Living Room", "Bedroom 1")
ground.connect("Dining", "Kitchen")
ground.connect("Bedroom 1", "Bathroom 1")

ground.add_window("Living Room", "west", 1.5, width=1.5)
ground.add_window("Dining", "east", 1.5, width=1.5)
ground.add_window("Study", "north", 1.4, width=1.2)
ground.add_window("Kitchen", "east", 0.9, width=1.2)
ground.add_window("Bedroom 1", "west", 0.9, width=1.2)
ground.add_window("Bathroom 1", "west", 0.7, width=0.6)
