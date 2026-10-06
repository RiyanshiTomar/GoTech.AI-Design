"""Reference answer for: 'Create a 20m x 30m house with 3 bedrooms, a living room, kitchen and 2 bathrooms.'"""
from archagent import Building

building = Building(width=20, depth=30, unit="m", setback=1, name="Family House")
building.declare_program(bedroom=3, bathroom=2, kitchen=1, living=1)

ground = building.add_floor("Ground Floor", elevation=0, height=3.0)

ground.add_room("Living Room", 1, 1, 7, 6)
ground.add_room("Dining", 8, 1, 5, 6)
ground.add_room("Kitchen", 13, 1, 6, 6)
ground.add_room("Corridor", 1, 7, 18, 2, kind="corridor")
ground.add_room("Bedroom 1", 1, 9, 5, 8)
ground.add_room("Bedroom 2", 6, 9, 6, 8)
ground.add_room("Bedroom 3", 12, 9, 7, 8)
ground.add_room("Bathroom 1", 1, 17, 4, 3)
ground.add_room("Bathroom 2", 12, 17, 4, 3)

ground.add_door("Living Room", "south", 2.5, width=1.2, entrance=True)
ground.connect("Living Room", "Dining")
ground.connect("Dining", "Kitchen")
ground.connect("Living Room", "Corridor")
ground.connect("Corridor", "Bedroom 1")
ground.connect("Corridor", "Bedroom 2")
ground.connect("Corridor", "Bedroom 3")
ground.connect("Bedroom 1", "Bathroom 1")
ground.connect("Bedroom 3", "Bathroom 2")

ground.add_window("Living Room", "west", 2)
ground.add_window("Living Room", "south", 5.2)
ground.add_window("Dining", "south", 1.8)
ground.add_window("Kitchen", "south", 2.4)
ground.add_window("Kitchen", "east", 2.4)
ground.add_window("Bedroom 1", "west", 3)
ground.add_window("Bedroom 2", "north", 2.4)
ground.add_window("Bedroom 3", "east", 3)
ground.add_window("Bathroom 1", "west", 1.2, width=0.6)
ground.add_window("Bathroom 2", "east", 1.2, width=0.6)
